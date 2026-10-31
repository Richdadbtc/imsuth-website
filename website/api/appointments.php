<?php
declare(strict_types=1);
require __DIR__ . '/bootstrap.php';
$data = require_post();
$date = text_field($data, 'preferredDate', 10, 10);
$parsed = DateTimeImmutable::createFromFormat('!Y-m-d', $date);
if (!$parsed || $parsed <= new DateTimeImmutable('today')) respond(422, ['ok' => false, 'field' => 'preferredDate', 'message' => 'Select a future date.']);
$patientType = text_field($data, 'patientType', 3, 16);
if (!in_array($patientType, ['new', 'existing'], true)) respond(422, ['ok' => false, 'field' => 'patientType', 'message' => 'Select a patient type.']);
if (($data['consent'] ?? false) !== true) respond(422, ['ok' => false, 'field' => 'consent', 'message' => 'Consent is required.']);
deliver('appointment', ['fullName'=>text_field($data,'fullName',2,120),'phone'=>phone_field($data,'phone'),'email'=>email_field($data,'email'),'patientType'=>$patientType,'department'=>text_field($data,'department',2,100),'preferredDoctor'=>text_field($data,'preferredDoctor',0,100,false),'preferredDate'=>$date,'preferredTime'=>text_field($data,'preferredTime',2,40),'reason'=>text_field($data,'reason',10,1500),'consent'=>true]);
