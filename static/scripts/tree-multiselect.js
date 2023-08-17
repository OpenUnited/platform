// options for multiselect tree

const options = [
  {
    name: 'Account management',
    value: 1,
    children: [
      {
        name: 'Sign up',
        value: 2,
        children: []
      },
      {
        name: 'User onboarding',
        value: 3,
        children: []
      },
      {
        name: 'Profile',
        value: 4,
        children: [
          {
            name: 'Personal details',
            value: 5,
            children: []
          },
          {
            name: 'Contributions',
            value: 6,
            children: []
          },
          {
            name: 'Status',
            value: 7,
            children: []
          },
        ]
      }
    ]
  },
  {
    name: 'Product management',
    value: 8,
    children: [
      {
        name: "Create and manage product",
        value: 9,
        children: []
      },
      {
        name: "Discover work",
        value: 10,
        children: []
      },
      {
        name: "Product summary",
        value: 11,
        children: []
      },
      {
        name: "Product Tree",
        value: 12,
        children: [
          {
            name: "Capabilities",
            value: 13,
            children: []
          }
        ]
      },
      {
        name: "Initiatives",
        value: 14,
        children: []
      },
      {
        name: "Task",
        value: 15,
        children: [
          {
            name: "Task claim",
            value: 16,
            children: [
              {
                name: "Request a task claim",
                value: 17,
                children: []
              },
              {
                name: "Withdraw task claim (Quit task)",
                value: 18,
                children: []
              },
              {
                name: "Review task claim",
                value: 19,
                children: [
                  {
                    name: "Accept task claim request",
                    value: 20,
                    children: []
                  },
                  {
                    name: "Reject task claim request",
                    value: 21,
                    children: []
                  }
                ]
              }
            ]
          },
          {
            name: "Contribution",
            value: 22,
            children: [
              {
                name: "Submit contibution",
                value: 23,
                children: []
              },
              {
                name: "Review contribution",
                value: 24,
                children: [
                  {
                    name: "Accept contribution",
                    value: 25,
                    children: []
                  },
                  {
                    name: "Reject contribution",
                    value: 26,
                    children: []
                  }
                ]
              },
              {
                name: "Delivery Message",
                value: 27,
                children: []
              }
            ]
          },
          {
            name: "Contribution destination",
            value: 28,
            children: []
          },
          {
            name: "Comments",
            value: 29,
            children: [
              {
                name: "Submit comment",
                value: 30,
                children: []
              },
              {
                name: "Mention user",
                value: 31,
                children: []
              },
              {
                name: "Update comment",
                value: 32,
                children: []
              },
              {
                name: "Delete comment",
                value: 33,
                children: []
              }
            ]
          },
          {
            name: "Task management",
            value: 34,
            children: []
          }
        ]
      },
      {
        name: "Product Setting",
        value: 35,
        children: [
          {
            name: "Product visibility (public / private)",
            value: 36,
            children: []
          },
          {
            name: "Policies",
            value: 37,
            children: [
              {
                name: "Set / Update Contribution License Agreement",
                value: 38,
                children: []
              }
            ]
          }
        ]
      },
      {
        name: "Product People",
        value: 39,
        children: []
      },
      {
        name: "Ideas & Bugs",
        value: 40,
        children: []
      },
      {
        name: "Guidelines",
        value: 41,
        children: [
          {
            name: "Contributing guidelines",
            value: 42,
            children: []
          }
        ]
      },
      {
        name: "Legal",
        value: 43,
        children: [
          {
            name: "Product license",
            value: 44,
            children: []
          },
          {
            name: "Contributor License Agreement (CLA)",
            value: 45,
            children: []
          }
        ]
      }
    ]
  }
]

const domElements = document.querySelectorAll('.treeselect-demo')

domElements.forEach((domElement) => {

  const treeselect = new Treeselect({
    parentHtmlContainer: domElement,
    value: [],
    options: options,
  })

  treeselect.srcElement.addEventListener('input', (e) => {
    console.log('Selected value:', e.detail)
  });

});
