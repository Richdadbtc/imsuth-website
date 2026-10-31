import getpass
import json
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError, PermissionDenied
from django.utils import timezone
from apps.accounts.models import User
from apps.catalogue.catalogue_setup import proposal,plan,apply,CONFIRM


class Command(BaseCommand):
    help='Preview or explicitly import proposed inactive hospital catalogue placeholders. No services or prices are seeded.'

    def add_arguments(self,parser):
        mode=parser.add_mutually_exclusive_group()
        mode.add_argument('--dry-run',action='store_true')
        mode.add_argument('--report',action='store_true')
        mode.add_argument('--apply',action='store_true')
        parser.add_argument('--actor',help='Existing active Super Administrator username; required for apply.')
        parser.add_argument('--reason',default='')
        parser.add_argument('--csv',help='Validated UTF-8 CSV file; omit to use the version-controlled master.')
        parser.add_argument('--select',action='append',help='Stable proposal key; repeat to select entries. Default: all proposed entries.')
        parser.add_argument('--plan-token',help='Preview fingerprint; required in production.')
        parser.add_argument('--confirm-production',default='',help='In production, explicitly supply: '+CONFIRM)

    def handle(self,*args,**options):
        try:
            content=None
            if options['csv']:
                with Path(options['csv']).open('rb') as stream:raw=stream.read(512*1024+1)
                if len(raw)>512*1024:raise CommandError('CSV exceeds 512KB.')
                content=raw.decode('utf-8-sig')
            data=proposal(content);selected=options['select']
            if options['apply']:
                if not options['actor']:raise CommandError('--apply requires an existing --actor username and --reason.')
                try:actor=User.objects.get(username=options['actor'])
                except User.DoesNotExist as error:raise CommandError('The specified actor does not exist.') from error
                selected=selected if selected is not None else [row['key'] for row in plan(data)['rows']]
                result=apply(data,selected,actor,options['reason'],plan_token=options['plan_token'],confirmation=options['confirm_production'])
            else:
                result=plan(data,selected)
                result['read_only']=True;result['initiated_by']=options['actor'] or 'OS operator: '+getpass.getuser()
            result['ran_at']=timezone.now().isoformat()
            self.stdout.write(json.dumps(result,indent=2,default=str))
        except (ValidationError,PermissionDenied,OSError,UnicodeError,ValueError) as error:
            raise CommandError('; '.join(error.messages) if isinstance(error,ValidationError) else str(error)) from error
