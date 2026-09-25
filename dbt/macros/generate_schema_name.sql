{#
  dbt's default generate_schema_name macro concatenates the profile's
  target schema with each model's `+schema` config (e.g. "staging_marts"
  instead of "marts"). We want raw/staging/marts as fixed, predictable
  schema names regardless of which target is active -- overriding this
  is the standard fix.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
