from apps.common import utils


def update_node_context(request, context, product_area):
    context["parent_id"] = int(request.POST.get("parent_id", 0))
    context["depth"] = int(request.POST.get("depth", 0))
    context["descendants"] = utils.serialize_tree(product_area)["children"]
    return "unauthenticated_tree/helper/add_node_partial.html"
