from drf_spectacular.extensions import OpenApiAuthenticationExtension


class AuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = 'knox.auth.TokenAuthentication'
    name = 'TokenAuthentication'

    def get_security_definition(self, auto_schema):
        return {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header'
        }
