select 
l.update_id as id,
l.tpl,
dep.ts as departure_ts,
dep.status as departure_status,
arr.ts as arrival_ts,
arr.status as arrival_status
from public."location" l 
left join public.service_update su on l.update_id = su.update_id 
left join public."timestamp" dep on l.departure_id = dep.ts_id 
left join public."timestamp" arr on l.arrival_id = arr.ts_id 
where su.rid = '202406187143949'