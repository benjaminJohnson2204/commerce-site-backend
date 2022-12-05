from rest_framework import pagination


class MyPagination(pagination.PageNumberPagination):
    def get_paginated_response(self, data):
        response = super(MyPagination, self).get_paginated_response(data)
        response.data["num_pages"] = self.page.paginator.num_pages
        return response
