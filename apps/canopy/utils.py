import random

from django.http import JsonResponse
from django.shortcuts import render

from apps.common import utils as common_utils
from apps.product_management import forms as mgt_forms, models as mgt

adjectives = [
    "Magnificent",
    "Exquisite",
    "Radiant",
    "Splendid",
    "Majestic",
    "Elegant",
    "Sublime",
    "Resplendent",
    "Impeccable",
    "Opulent",
    "Grandiose",
    "Stupendous",
    "Glorious",
    "Enchanting",
    "Effervescent",
    "Brilliant",
    "Luminous",
    "Dazzling",
    "Vibrant",
    "Stellar",
    "Sparkling",
    "Glistening",
    "Shimmering",
    "Lustrous",
    "Fabulous",
    "Marvelous",
    "Stunning",
    "Radiant",
    "Glowing",
    "Awe-inspiring",
]

trees = [
    "Maple",
    "Birch",
    "Oak",
    "Elm",
    "Ash",
    "Pine",
    "Cedar",
    "Fir",
    "Beech",
    "Palm",
    "Spruce",
    "Larch",
    "Alder",
    "Willow",
    "Ebony",
    "Yew",
    "Holly",
    "Fig",
    "Rowan",
    "Teak",
    "Lime",
    "Cork",
    "Mango",
    "Apple",
    "Pear",
    "Plum",
    "Cherry",
    "Peach",
    "Palm",
]


def generate_unique_name():
    adjective = random.choice(adjectives)
    noun = random.choice(trees)
    number = random.randint(100, 999)
    return f"{adjective} {noun} {number}"


def add_node_helper(request, product_area, context):
    form = mgt_forms.ProductAreaForm(request.POST)
    if not form.is_valid():
        return JsonResponse({"error": "Something went wrong."}, status=400)

    context["node"] = [common_utils.serialize_tree(product_area.add_child(**form.cleaned_data))]
    context["parent"] = product_area
    context["depth"] = int(request.POST.get("depth", 0))
    context["margin_left"] = int(request.POST.get("margin_left", 0))
    context["can_modify_product"] = True
    return render(request, "product_tree/components/partials/add_node_partial.html", context)


def update_node_helper(request, product_area):
    form = mgt_forms.ProductAreaForm(request.POST)
    has_dropped = bool(request.POST.get("has_dropped", False))
    parent_id = request.POST.get("parent_id")
    has_cancelled = bool(request.POST.get("cancelled", False))

    if not has_cancelled and has_dropped and parent_id:
        parent = mgt.ProductArea.objects.get(pk=parent_id)
        product_area.move(parent, "last-child")
        talent_target_parent = product_area.get_parent() or 0
        context = {
            "child_count": (
                talent_target_parent.get_children_count() if isinstance(talent_target_parent, mgt.ProductArea) else 0
            ),
            "target_parent_id": talent_target_parent.id if talent_target_parent else None,
        }
        return JsonResponse(context)

    if not has_cancelled and form.is_valid():
        product_area.name = form.cleaned_data["name"]
        product_area.description = form.cleaned_data["description"]
        product_area.save()

    context = {
        "product_area": product_area,
        "parent_id": parent_id or 0,
        "node": [common_utils.serialize_tree(product_area)],
        "depth": int(request.POST.get("depth", 0)),
        "can_modify_product": True,
    }
    return render(request, "product_tree/components/partials/add_node_partial.html", context)


def add_root_node_helper(request, tree_id, context):
    form = mgt_forms.ProductAreaForm(request.POST)
    if not form.is_valid():
        return JsonResponse({"error": "Something went wrong."}, status=400)

    product_area = mgt.ProductArea.add_root(**form.cleaned_data, product_tree_id=tree_id)
    context["product_area"] = product_area
    context["depth"] = int(request.POST.get("depth", 0)) + 1
    context["margin_left"] = int(request.POST.get("margin_left", 0))
    context["can_modify_product"] = True
    context["node"] = [common_utils.serialize_tree(product_area)]
    context["id"] = product_area.pk
    return render(request, "product_tree/components/partials/add_node_partial.html", context)


def shareable_tree_helper(request, product_tree, show_share_button=False):
    domain = f"{request.scheme}://{request.get_host()}"
    return {
        "can_modify_product": True,
        "product_tree": product_tree,
        "sharable_link": f"{domain}/product-tree/share/{product_tree.pk}",
        "tree_data": [common_utils.serialize_tree(node) for node in product_tree.product_areas.filter(depth=1)],
        "show_share_button": show_share_button,
        "margin_left": int(request.GET.get("margin_left", 0)),
        "depth": int(request.GET.get("depth", 0)),
    }
