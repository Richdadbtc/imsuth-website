<?php
declare(strict_types=1);
require __DIR__ . '/bootstrap.php';
$data = require_post();
deliver('contact', ['name'=>text_field($data,'name',2,120),'email'=>email_field($data,'email'),'phone'=>phone_field($data,'phone',false),'subject'=>text_field($data,'subject',2,160),'message'=>text_field($data,'message',10,3000)]);
