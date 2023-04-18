class Routes(object):
    def __init__(self, api):

        from src.api.execute_universal_query import ApiQuery

        api.add_resource(ApiQuery, "/universal_query")
        from src.api.cms import CMS

        api.add_resource(CMS, "/cms_management")
        from src.api.login import Login

        api.add_resource(Login, "/login")
