import uuid

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import generic

from apps.canopy import utils
from apps.common import utils as common_utils
from apps.product_management import models as mgt


def introduction(request):
    return render(request, "introduction.html")


def chapter1(request):
    return render(request, "chapter-1.html")


def share_tree_link(request):
    return redirect(f'{reverse("shareable_product_tree")}?key={request.GET.get("key", None)}')


class ProductTreeView(generic.CreateView):
    template_name = "unauthenticated_tree/index.html"
    model = mgt.ProductTree
    fields = ["name"]

    def get_context_data(self, **kwargs):
        if key := self.request.GET.get("key", None):
            product_tree = get_object_or_404(mgt.ProductTree, pk=key)
            show_share_button = False

        else:
            if "tree_session_id" not in self.request.session:
                session_id = str(uuid.uuid4())
                self.request.session["tree_session_id"] = session_id
            else:
                session_id = self.request.session["tree_session_id"]

            product_tree = mgt.ProductTree.objects.filter(session_id=session_id).first()

            if not product_tree:
                product_tree = mgt.ProductTree.objects.create(name=utils.generate_unique_name(), session_id=session_id)
                mgt.ProductArea.add_root(
                    name="Product Area",
                    description="Description of Product Area",
                    product_tree=product_tree,
                )
            show_share_button = True

        domain = f"{self.request.scheme}://{self.request.get_host()}"
        return {
            "can_modify_product": True,
            "product_tree": product_tree,
            "sharable_link": f"{domain}/product-tree/share/?key={product_tree.pk}",
            "tree_data": [common_utils.serialize_tree(node) for node in product_tree.product_areas.filter(depth=1)],
            "show_share_button": show_share_button,
            "margin_left": int(self.request.GET.get("margin_left", 0)),
            "depth": int(self.request.GET.get("depth", 0)),
        }


class ProductTreeUpdateView(generic.UpdateView):
    template_name = "unauthenticated_tree/index.html"
    model = mgt.ProductTree
    fields = ["name"]

    def form_valid(self, form):
        obj = form.save()
        return JsonResponse({"name": obj.name})

    def form_invalid(self, form):
        return JsonResponse({"error": "This name isn't available"}, status=400)


def reset_tree(request):
    request.session.pop("tree_session_id", None)
    return redirect(reverse("shareable_product_tree"))


def add_root_node(request, tree_id):
    context = {}
    if request.method == "POST":
        return utils.add_root_node_helper(request, tree_id, context)

    context["can_modify_product"] = True
    context["depth"] = int(request.POST.get("depth", 0)) + 1
    context["tree_id"] = tree_id
    context["id"] = str(uuid.uuid4())[:8]
    return render(request, "product_tree/components/partials/create_root_node_partial.html", context)


def add_node(request, parent_id):
    product_area = mgt.ProductArea.objects.get(pk=parent_id)
    context = {}
    if request.method == "POST":
        return utils.add_node_helper(request, product_area, context)
    context["id"] = str(uuid.uuid4())[:8]
    context["margin_left"] = int(request.GET.get("margin_left", 0)) + 4
    context["depth"] = int(request.GET.get("depth", 0)) + 1
    context["parent_id"] = product_area.id
    context["product_area"] = product_area
    context["can_modify_product"] = True
    return render(request, "product_tree/components/partials/create_node_partial.html", context)


def delete_node(request, pk):
    product_area = mgt.ProductArea.objects.get(pk=pk)
    parent = product_area.get_parent() or None

    if product_area.numchild > 0:
        return JsonResponse({"error": "Unable to delete a node with a child."}, status=400)
    product_area.delete()
    context = {
        "message": "The node has deleted successfully",
        "parent_id": parent.id if parent else None,
        "parent_child_count": parent.get_children_count() if parent else 0,
    }
    return JsonResponse(context)


def update_node(request, pk):
    product_area = mgt.ProductArea.objects.get(pk=pk)
    if request.method == "POST":
        return utils.update_node_helper(request, product_area)
    context = {
        "margin_left": int(request.GET.get("margin_left", 0)) + 4,
        "parent_id": product_area.id,
        "depth": int(request.GET.get("depth", 0)),
        "product_area": product_area,
        "can_modify_product": True,
    }
    return render(request, "product_tree/components/partials/update_node_partial.html", context)
