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
    signup_date::date as signup_date,
    member_status,
    cancellation_date::date as cancellation_date,
    gender,
    acquisition_channel,
    primary_goal,
    age_band
from read_csv_auto('data/members.csv');

create or replace table fct_member_day as
select
    e.member_id,
    e.event_date,
    any_value(m.cohort) as cohort,
    any_value(m.plan_type) as plan_type,
    any_value(m.member_status) as member_status,
    any_value(m.gender) as gender,
    any_value(m.acquisition_channel) as acquisition_channel,
    any_value(m.primary_goal) as primary_goal,
    any_value(m.age_band) as age_band,
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

create or replace table agg_member_lifecycle as
with activity as (
    select
        member_id,
        max(event_date) as last_active_date,
        count(distinct event_date) as active_days_observed,
        count(distinct case when event_date >= current_date - interval 30 day then event_date end) as active_days_30d
    from fct_member_day
    group by 1
),
member_base as (
    select
        m.*,
        coalesce(a.active_days_observed, 0) as active_days_observed,
        coalesce(a.active_days_30d, 0) as active_days_30d,
        a.last_active_date,
        case when m.signup_date >= current_date - interval 30 day then 1 else 0 end as is_new_30d,
        case when coalesce(a.active_days_30d, 0) > 0 then 1 else 0 end as is_active_30d,
        case when m.signup_date <= current_date - interval 30 day then 1 else 0 end as retention_eligible
    from dim_members m
    left join activity a on m.member_id = a.member_id
)
select
    cohort,
    gender,
    plan_type,
    primary_goal,
    acquisition_channel,
    count(*) as total_members,
    sum(is_new_30d) as new_members_30d,
    sum(is_active_30d) as active_members_30d,
    sum(case when member_status = 'churned' then 1 else 0 end) as churned_members,
    round(sum(is_active_30d) * 100.0 / nullif(count(*), 0), 1) as subscription_continuity_pct,
    round(
        sum(case when retention_eligible = 1 and is_active_30d = 1 then 1 else 0 end) * 100.0
        / nullif(sum(retention_eligible), 0),
        1
    ) as retention_rate_pct,
    round(avg(active_days_30d), 1) as avg_active_days_30d
from member_base
group by 1, 2, 3, 4, 5;

create or replace table metric_dictionary as
select * from (
    values
    ('new_members_30d', 'Members whose signup date occurred in the last 30 days.', 'dim_members.signup_date >= current_date - interval 30 day', 'Growth'),
    ('retention_rate_pct', 'Percent of retention-eligible members active in the last 30 days.', 'active_members_30d / retention_eligible_members', 'Retention'),
    ('subscription_continuity_pct', 'Percent of members with recent activity, grouped by plan and cohort.', 'active_members_30d / total_members', 'Subscription'),
    ('avg_recovery', 'Average daily recovery score by cohort.', 'fct_member_day.recovery_score', 'Member Insights'),
    ('avg_sleep_hours', 'Average sleep duration in hours.', 'fct_member_day.sleep_minutes / 60', 'Member Insights'),
    ('avg_strain', 'Average daily strain score.', 'fct_member_day.daily_strain', 'Member Insights'),
    ('low_recovery_pct', 'Percent of member-days with recovery below 45.', 'fct_member_day.recovery_score < 45', 'Risk Signals'),
    ('low_engagement_pct', 'Percent of member-days with app usage under two minutes.', 'fct_member_day.app_session_minutes < 2', 'Risk Signals'),
    ('event_count', 'Number of raw wearable or app events contributing to a member-day.', 'stg_member_events.event_id', 'Data Quality'),
    ('freshness_hours', 'Hours since the latest event in the raw event table.', 'max(stg_member_events.event_ts)', 'Platform Health')
) as t(metric_name, definition, source_logic, domain);

create or replace table pipeline_run_log as
select
    current_timestamp as run_completed_at,
    'success' as status,
    (select count(*) from stg_member_events) as raw_events,
    (select count(*) from dim_members) as members,
    (select count(*) from fct_member_day) as member_days,
    (select count(*) from agg_cohort_daily) as cohort_days,
    (select count(*) from agg_member_lifecycle) as lifecycle_segments,
    (select round(date_diff('minute', max(event_ts), current_timestamp) / 60.0, 1) from stg_member_events) as freshness_hours;

create or replace table model_inventory as
select * from (
    values
    ('stg_member_events', 'event', 'one row per wearable/app event', (select count(*) from stg_member_events)),
    ('dim_members', 'dimension', 'one row per member', (select count(*) from dim_members)),
    ('fct_member_day', 'fact', 'one row per member per active day', (select count(*) from fct_member_day)),
    ('agg_cohort_daily', 'aggregate', 'one row per cohort per day', (select count(*) from agg_cohort_daily)),
    ('agg_member_lifecycle', 'aggregate', 'one row per lifecycle segment', (select count(*) from agg_member_lifecycle)),
    ('metric_dictionary', 'governance', 'one row per governed metric', (select count(*) from metric_dictionary)),
    ('pipeline_run_log', 'audit', 'one row per pipeline build', (select count(*) from pipeline_run_log))
) as t(model_name, model_type, grain, row_count);
