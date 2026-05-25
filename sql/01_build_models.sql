create or replace table stg_member_events as
select
    event_id,
    member_id,
    event_ts,
    cast(event_ts as date) as event_date,
    event_type,
    heart_rate,
    strain,
    sleep_minutes,
    recovery_score,
    app_session_minutes,
    workout_minutes
from read_csv_auto('data/member_events.csv');

create or replace table dim_members as
select
    member_id,
    cohort,
    plan_type,
    signup_date,
    primary_goal,
    age_band
from read_csv_auto('data/members.csv');

create or replace table fct_member_day as
select
    e.member_id,
    e.event_date,
    any_value(m.cohort) as cohort,
    any_value(m.plan_type) as plan_type,
    any_value(m.primary_goal) as primary_goal,
    round(avg(e.heart_rate), 1) as avg_heart_rate,
    round(max(e.strain), 1) as daily_strain,
    max(e.sleep_minutes) as sleep_minutes,
    max(e.recovery_score) as recovery_score,
    sum(e.app_session_minutes) as app_session_minutes,
    sum(e.workout_minutes) as workout_minutes,
    count(*) as event_count
from stg_member_events e
join dim_members m on e.member_id = m.member_id
group by 1, 2;

create or replace table agg_cohort_daily as
select
    event_date,
    cohort,
    count(distinct member_id) as active_members,
    round(avg(recovery_score), 1) as avg_recovery,
    round(avg(sleep_minutes) / 60, 2) as avg_sleep_hours,
    round(avg(daily_strain), 1) as avg_strain,
    round(avg(app_session_minutes), 1) as avg_app_minutes,
    round(sum(case when recovery_score < 45 then 1 else 0 end) * 100.0 / count(*), 1) as low_recovery_pct,
    round(sum(case when app_session_minutes < 2 then 1 else 0 end) * 100.0 / count(*), 1) as low_engagement_pct
from fct_member_day
group by 1, 2;

create or replace table metric_dictionary as
select * from (
    values
    ('avg_recovery', 'Average daily recovery score by cohort.', 'fct_member_day.recovery_score', 'Member Insights'),
    ('avg_sleep_hours', 'Average sleep duration in hours.', 'fct_member_day.sleep_minutes / 60', 'Member Insights'),
    ('avg_strain', 'Average daily strain score.', 'fct_member_day.daily_strain', 'Member Insights'),
    ('low_recovery_pct', 'Percent of member-days with recovery below 45.', 'fct_member_day.recovery_score < 45', 'Risk Signals'),
    ('low_engagement_pct', 'Percent of member-days with app usage under two minutes.', 'fct_member_day.app_session_minutes < 2', 'Risk Signals'),
    ('event_count', 'Number of raw wearable or app events contributing to a member-day.', 'stg_member_events.event_id', 'Data Quality')
) as t(metric_name, definition, source_logic, domain);

create or replace table pipeline_run_log as
select
    current_timestamp as run_completed_at,
    'success' as status,
    (select count(*) from stg_member_events) as raw_events,
    (select count(*) from dim_members) as members,
    (select count(*) from fct_member_day) as member_days,
    (select count(*) from agg_cohort_daily) as cohort_days;
