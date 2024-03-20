$(function () {
  $("#jstree_demo")
    .jstree({
      core: {
        multiple: false,
        animation: 100,
        check_callback: true,
        themes: {
          variant: "medium",
          dots: false,
        },
      },
      types: {
        default: {
          icon: "glyphicon glyphicon-flash",
        },
        demo: {
          icon: "glyphicon glyphicon-th-large",
        },
      },
      conditionalselect: function (node, event) {
        return false;
      },
      plugins: [
        "dnd",
        "massload",
        "search",
        "state",
        "types",
        "unique",
        "wholerow",
        "changed",
        "conditionalselect",
      ],
      search: {
        show_only_matches: true,
        show_only_matches_children: true,
      },
    })
    .on("show_contextmenu.jstree", function (e, data) {})
    .on("search.jstree", function (nodes, str, res) {
      if (str.nodes.length === 0) {
        $("#jstree_demo").jstree(true).hide_all();
        $(".search_empty").removeClass("hidden");
      } else {
        $(".search_empty").addClass("hidden");
      }
    });
});

$("#AddFirst").on("click", create_node);
const newNode = (text, id) => {
  let newNodeText = ` <div
  class="nested-item__label shadow-inner h-max flex items-start w-full gap-2 group/item py-3 hover:bg-light-blue px-2 transition-all ease-linear duration-200 rounded">
  <div class="flex flex-col w-full">
    <div class="flex w-full justify-between items-center">
      <div class="flex items-center gap-1">
        <button class="w-3 h-3">
          <img src="/static/images/drag.svg" class="w-full h-full object-contain object-center" alt="#">
        </button>
        <span class="flex flex-wrap items-center font-semibold">
          <a href="{{item['link']}}"
            class="tree-text mr-2 text-base text-dark group-hover/item:text-blue-400 transition-all ease-linear duration-200">${
              text || "New item"
            }</a>
          <input type="text" class="hidden mr-2 text-base text-dark rename_input border border-light-gray rounded" />
        </span>
      </div>
      <div class="flex gap-3 items-center">
        <button class="add_node w-5 h-5">
           <img src="/static/images/add.svg" class="" alt="#">
        </button>
        <button class="edit_node w-5 h-5">
          <img src="/static/images/edit_icon.svg" class="" alt="#">
        </button>
        <button class="check_node w-5 h-5 hidden">
            <img src="/static/images/check-green.svg" class="check" alt="#">
          </button>
        <button class="delete_node w-5 h-5 ">
          <img src="/static/images/delete.svg" class="" alt="#">
        </button>
      </div>
    </div>
      <span class="text_desc flex text-sm leading-6 text-gray-700 font-normal mt-0.5"></span>
    <input type="text" class="hidden ml-4 mr-2 text-base text-dark renameDesc_input mt-2 border border-light-gray rounded" placeholder="Add description" />
    <span class="hidden">${id}</span>
  </div>
  </div>`;
  return newNodeText;
};

function create_node() {
  clearSearchNode();
  $(".search_empty").addClass("hidden");
  let ref = $("#jstree_demo").jstree(true),
    sel = ref.get_selected();
  if (!sel.length) {
    sel[0] = "#";
  }
  sel = sel[0];

  sel = ref.create_node(sel, { text: newNode(null, Math.random()) }, "first");
}

const setupDeleteNode = () => {
  $("#jstree_demo").on("click", ".delete_node", function (e) {
    e.stopPropagation();
    const closestLi = $(this).closest("li")[0];
    $("#jstree_demo").jstree("delete_node", closestLi.id);
  });
};

const setupEditNode = () => {
  $("#jstree_demo").on("click", ".edit_node", function (event) {
    event.stopPropagation();
    $(this).addClass("hidden");
    $(this).siblings(".check_node").removeClass("hidden");
    const label = $(this).closest(".nested-item__label");
    const a = $(this).closest(".jstree-anchor");
    a.removeClass();
    a.addClass("flex ml-5 mt-[-30px] relative focus-visible:outline-0");
    const treeText = label.find(".tree-text");
    const treeDescText = label.find(".text_desc");
    const input = label.find(".rename_input");
    const descInput = label.find(".renameDesc_input");
    inputChange(treeText, input, true);
    inputChange(treeDescText, descInput);
  });
};
const inputChange = (treeText, input, focus) => {
  treeText.addClass("hidden");
  input.removeClass("hidden");
  input.val(treeText.text());
  if (focus) {
    input.focus();
  }
};
const inputChangeSave = (treeText, input) => {
  treeText.removeClass("hidden");
  input.addClass("hidden");
  treeText.text(input.val());
};
const saveEditNode = () => {
  $("#jstree_demo").on("click", ".check_node", function (e) {
    e.stopPropagation();
    $(this).addClass("hidden");
    $(this).siblings(".edit_node").removeClass("hidden");
    const label = $(this).closest(".nested-item__label");
    var li = e.target.closest("li");
    const input = label.find(".rename_input");
    const descInput = label.find(".renameDesc_input");
    const treeText = label.find(".tree-text");
    const treeDescText = label.find(".text_desc");
    const parentElement = e.target.closest(".nested-item__label");
    const a = $(this).closest(".jstree-anchor");
    inputChangeSave(treeText, input);
    inputChangeSave(treeDescText, descInput);
    a.removeClass();
    a.addClass("jstree-anchor");
    $("#jstree_demo").jstree("rename_node", li.id, parentElement.outerHTML);
    saveEditNode();


    var data = {
      "id":li.id,
      "name":input.val(),
      "description":descInput.val(),
      "data_parent_id": $(li).attr("data-parent-li-id"),
      "csrfmiddlewaretoken": $("#csrf_token_id").val(),
      "new_node":  $(li).attr("data-new-node")=="true"? true: false,
    }

    if (data["new_node"] == true){
      $.ajax({
        url: $(li).attr("data-url-post") ,
        method: "POST",
        data: data,
        success: function(data) {
            console.log(data);
        }
      });
    }
    else{
      $.ajax({
        url: $(li).attr("data-url-update") ,
        method: "POST",
        data: data,
        success: function(data) {
            console.log(data);
        }
      });
    }

  });
};

const setupCreateNode = () => {
  $("#jstree_demo").on("click", ".add_node", function (e) {
    e.stopPropagation();
    const parentNode = $(this).closest("li")[0];


    const id = $("#jstree_demo").jstree(
      "create_node",
      parentNode.id,
      {
        text: newNode(null, Math.random()),
      },
      "first"
    );

    $("#"+id).attr("data-parent-li-id", $(parentNode).attr("data-id"))
    $("#"+id).attr("data-new-node", true)
    $("#"+id).attr("data-url-post", $(parentNode).attr("data-url-post"))


    $("#jstree_demo").jstree(true).open_node(parentNode.id);

  });
};
const viewVideo = () => {
  const videoBtnsOpen = document.querySelectorAll(".btn-video__open");
  const modalWrap = document.querySelector(".modal-wrap");
  const modalWrapCloseBtn = document.querySelector(".btn-video__close");

  if (modalWrap) {
    modalWrap.querySelector("iframe").src = "";
  }
  videoBtnsOpen.forEach((btn) => {
    btn.addEventListener("click", () => {
      modalWrap.classList.remove("hidden");
      modalWrap.querySelector("iframe").src = btn.dataset.video;
    });
  });

  if (modalWrapCloseBtn) {
    modalWrapCloseBtn.addEventListener("click", () => {
      modalWrap.classList.add("hidden");
    });
  }
};
const searchNode = () => {
  $("#search-field").keyup(function () {
    if ($(this).val().trim() === "") {
      $(".search_empty").addClass("hidden");
    }
    $("#jstree_demo").jstree(true).show_all();
    $(".jstree-node").show();
    $("#jstree_demo").jstree("search", $(this).val());
    $(".jstree-hidden").hide();
    $("a.jstree-search").parent("li").find(".jstree-hidden").show();
  });
};
const clearSearchNode = () => {
  $("#search-field").val("").change().focus();
};
$(document).ready(function () {
  setupDeleteNode();
  setupEditNode();
  setupCreateNode();
  searchNode();
  saveEditNode();
});

$("#jstree_demo").on("before_open.jstree", function (e, data) {
  viewVideo();
});

$(document).on("click", ".jstree-anchor", function (e) {
  var dataId = $(this).attr("id");


  // window.location.href = window.origin + "/product/product-area-detail";
});

const quill = new Quill("#editor", {
  modules: {
    syntax: true,
    toolbar: "#toolbar-container",
  },
  placeholder: "Compose an epic...",
  theme: "snow",
});
