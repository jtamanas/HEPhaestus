Schema test fixtures
====================

relic_singletDM_synthetic.json
  Valid relic/v1 fixture. Singlet DM benchmark at m_DM=62.5 GeV.
  Expected: validates against relic.schema.json with no errors.

annihilation_singletDM_synthetic.json
  Valid annihilation/v1 fixture. Singlet DM benchmark at m_DM=62.5 GeV.
  Expected: validates against annihilation.schema.json with no errors.

relic_invalid_extra_field.json
  INVALID. Contains _failure_mode key that violates additionalProperties:false.
  Expected: jsonschema.Draft202012Validator raises ValidationError (additionalProperties).

annihilation_invalid_negative.json
  INVALID. sigma_v_zero is set to -1.0, violating minimum:0.
  Expected: jsonschema.Draft202012Validator raises ValidationError (minimum 0 / negative value).
