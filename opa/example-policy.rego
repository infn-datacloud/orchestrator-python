# The policy returns the roles granted to a user identified by a trused issuer.
# Roles are stored in the "groups" attribute of the JWT token.
#
# This policy does:
#
#	* Extract and decode a JSON Web Token (JWT).
#	* Verify signatures on JWT using built-in functions in Rego.
#	* Define helper rules that provide useful abstractions.
#   * Verify token's iss is a trusted issuer.
#   * Retrieve roles granted to authenticated user.
#
# For more information see:
#
#	* Rego JWT decoding and verification functions:
#     https://www.openpolicyagent.org/docs/latest/policy-reference/#token-verification
#
package orchestrator

import rego.v1

default is_user := false

is_user if {
	some issuer in data.trusted_issuers
	issuer == claims.iss
}

default is_admin := false

is_admin if {
	is_user
	some role in claims.groups
	role == data.admin_entitlement
}

default allow := false

# Allow if user is admin
allow if {
	is_admin
}

# Allow to create a user with a different sub only if admin
allow if {
	is_user
	input.method == "POST"
	input.path == "/api/v1/users/"
	input.body == null
}

# Allow users on permitted endpoints
allow if {
	is_user
	some endpoint in data.user_endpoints
	endpoint.method == input.method
	endpoint.path == input.path
}

claims := payload if {
	# This statement invokes the built-in function `io.jwt.decode` passing the
	# parsed bearer_token as a parameter. The `io.jwt.decode` function returns an
	# array:
	#
	#	[header, payload, signature]
	#
	# In Rego, you can pattern match values using the `=` and `:=` operators. This
	# example pattern matches on the result to obtain the JWT payload.
	[_, payload, _] := io.jwt.decode(bearer_token)
}

bearer_token := t if {
	# Bearer tokens are contained inside of the HTTP Authorization header. This rule
	# parses the header and extracts the Bearer token value. If no Bearer token is
	# provided, the `bearer_token` value is undefined.
	v := input.headers.authorization
	startswith(v, "Bearer ")
	t := substring(v, count("Bearer "), -1)
}
