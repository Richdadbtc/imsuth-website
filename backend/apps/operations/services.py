import csv
import hashlib
import io
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.auditlog.models import AuditEvent
from apps.payments.models import Payment
from .models import ApprovalDecision, ApprovalRequest, ReconciliationBatch, ReconciliationItem, Refund, Reversal


def request_refund(*, payment, amount, reason, requested_by):
    if payment.status != Payment.Status.CONFIRMED:
        raise ValidationError("Only confirmed payments can be refunded.")
    amount = Decimal(amount)
    if amount <= 0 or amount > payment.amount:
        raise ValidationError("Refund amount is outside the allowed range.")
    with transaction.atomic():
        approval = ApprovalRequest.objects.create(request_type=ApprovalRequest.Type.REFUND, requested_by=requested_by, object_type="payments.Payment", object_id=str(payment.pk), amount=amount, reason=reason)
        refund = Refund.objects.create(payment=payment, amount=amount, reason=reason, requested_by=requested_by, approval=approval)
        AuditEvent.record("refund.requested", actor=requested_by, obj=refund, reason=reason)
        return refund


def request_reversal(*, payment, reason, requested_by):
    if payment.status != Payment.Status.CONFIRMED:
        raise ValidationError("Only confirmed payments can be considered for reversal.")
    with transaction.atomic():
        approval = ApprovalRequest.objects.create(request_type=ApprovalRequest.Type.REVERSAL, requested_by=requested_by, object_type="payments.Payment", object_id=str(payment.pk), amount=payment.amount, reason=reason)
        reversal = Reversal.objects.create(payment=payment, reason=reason, requested_by=requested_by, approval=approval)
        AuditEvent.record("reversal.requested", actor=requested_by, obj=reversal, reason=reason)
        return reversal


def decide_approval(*, approval, approver, approved, reason):
    if approval.request_type == "catalogue_activation":
        from apps.catalogue.catalogue_approvals import decide_activation
        return decide_activation([approval.pk], approver, approved, reason)[0]
    if approver.pk == approval.requested_by_id:
        raise PermissionDenied("The maker cannot approve their own request.")
    if not approver.has_paypoint_role(User.Role.FINANCE, User.Role.MANAGEMENT):
        raise PermissionDenied("This role cannot decide financial approvals.")
    with transaction.atomic():
        locked = ApprovalRequest.objects.select_for_update().get(pk=approval.pk)
        if locked.status != ApprovalRequest.Status.PENDING:
            raise ValidationError("Approval request has already been decided.")
        locked.status = ApprovalRequest.Status.APPROVED if approved else ApprovalRequest.Status.REJECTED
        locked.save(update_fields=("status", "updated_at"))
        decision = ApprovalDecision.objects.create(request=locked, decided_by=approver, approved=approved, reason=reason)
        if locked.request_type == ApprovalRequest.Type.REFUND:
            refund = locked.refund
            refund.status = Refund.Status.APPROVED_PENDING_EXECUTION if approved else Refund.Status.REJECTED
            refund.save(update_fields=("status", "updated_at"))
            if approved:
                payment = Payment.objects.select_for_update().get(pk=refund.payment_id)
                payment.status = Payment.Status.REFUND_PENDING
                payment.save(update_fields=("status", "updated_at"))
        elif locked.request_type == ApprovalRequest.Type.REVERSAL:
            reversal = locked.reversal
            reversal.status = Reversal.Status.APPROVED_PENDING_EXECUTION if approved else Reversal.Status.REJECTED
            reversal.save(update_fields=("status", "updated_at"))
            if approved:
                payment = Payment.objects.select_for_update().get(pk=reversal.payment_id)
                payment.status = Payment.Status.REVERSAL_PENDING
                payment.save(update_fields=("status", "updated_at"))
        elif locked.request_type == ApprovalRequest.Type.MANUAL_MATCH and approved:
            item = ReconciliationItem.objects.select_for_update().get(pk=locked.object_id)
            item.status = ReconciliationItem.Status.RESOLVED
            item.resolution_reason = reason
            item.save(update_fields=("status", "resolution_reason", "updated_at"))
        AuditEvent.record("approval.decided", actor=approver, obj=locked, reason=reason, metadata={"approved": approved})
        return decision


def auto_match_item(item):
    payment = Payment.objects.filter(status=Payment.Status.CONFIRMED).filter(
        models_q_reference(item.external_reference)
    ).first()
    if payment is None:
        item.status = ReconciliationItem.Status.UNMATCHED
    elif payment.amount == item.amount and payment.currency == item.currency:
        item.payment = payment
        item.status = ReconciliationItem.Status.MATCHED
    else:
        item.payment = payment
        item.status = ReconciliationItem.Status.AMOUNT_MISMATCH
    item.save(update_fields=("payment", "status", "updated_at"))
    return item


def models_q_reference(reference):
    from django.db.models import Q
    return Q(reference=reference) | Q(provider_reference=reference)


def import_reconciliation_csv(*, content, source, imported_by):
    digest = hashlib.sha256(content).hexdigest()
    if ReconciliationBatch.objects.filter(file_digest=digest).exists():
        raise ValidationError("This reconciliation file was already imported.")
    text = content.decode("utf-8-sig")
    rows = list(csv.DictReader(io.StringIO(text)))
    required = {"reference", "amount", "currency", "transaction_date"}
    if not rows or not required.issubset(rows[0]):
        raise ValidationError("CSV requires reference, amount, currency and transaction_date columns.")
    if len(rows) > 10000:
        raise ValidationError("A statement may contain at most 10,000 rows.")
    parsed = []
    references = set()
    for row in rows:
        try:
            amount = Decimal(row["amount"])
            reference = row["reference"]
            currency = row["currency"]
            if not reference or len(reference)>160 or reference in references:
                raise ValueError("Invalid or duplicate reference")
            if not amount.is_finite() or amount<0 or amount>=Decimal("100000000000000000") or amount.as_tuple().exponent < -2:
                raise ValueError("Invalid amount")
            if not currency or len(currency)!=3 or not currency.isalpha() or currency!=currency.upper():
                raise ValueError("Invalid currency")
            references.add(reference)
            occurred = datetime.fromisoformat(row["transaction_date"])
            if timezone.is_naive(occurred):
                occurred = timezone.make_aware(occurred)
        except (InvalidOperation, ValueError, TypeError, KeyError) as exc:
            raise ValidationError("Invalid reconciliation row.") from exc
        parsed.append((row, amount, occurred))
    dates = [entry[2].date() for entry in parsed]
    with transaction.atomic():
        batch = ReconciliationBatch.objects.create(source=source, period_start=min(dates), period_end=max(dates), file_digest=digest, imported_by=imported_by, total_amount=sum((entry[1] for entry in parsed), Decimal("0.00")))
        for row, amount, occurred in parsed:
            item = ReconciliationItem.objects.create(batch=batch, external_reference=row["reference"], amount=amount, currency=row["currency"], transaction_date=occurred)
            auto_match_item(item)
        if batch.items.exclude(status=ReconciliationItem.Status.MATCHED).exists():
            batch.status = ReconciliationBatch.Status.REVIEW_REQUIRED
        else:
            batch.status = ReconciliationBatch.Status.RECONCILED
        batch.save(update_fields=("status", "updated_at"))
        AuditEvent.record("reconciliation.imported", actor=imported_by, obj=batch, metadata={"rows": len(parsed)})
        return batch
