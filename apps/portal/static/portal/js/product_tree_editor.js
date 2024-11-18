function initializeTree() {
    // Get container and data
    const container = document.getElementById('tree-editor');
    if (!container) return;

    try {
        const data = JSON.parse(container.getAttribute('data-tree-data'));
        console.log('Tree data:', data);

        // Basic SVG setup
        const svg = d3.select('#tree-editor')
            .append('svg')
            .attr('width', 800)
            .attr('height', 600);

        // Create hierarchy
        const root = d3.hierarchy(data);

        // Create basic tree layout
        const treeLayout = d3.tree()
            .size([500, 700]);

        // Generate tree data
        treeLayout(root);

        // Create a group for the tree
        const g = svg.append('g')
            .attr('transform', 'translate(50,50)');

        // Add the links (edges)
        g.selectAll('.link')
            .data(root.links())
            .enter()
            .append('path')
            .attr('class', 'link')
            .attr('d', d3.linkHorizontal()
                .x(d => d.y)
                .y(d => d.x));

        // Add the nodes
        const nodes = g.selectAll('.node')
            .data(root.descendants())
            .enter()
            .append('g')
            .attr('class', 'node')
            .attr('transform', d => `translate(${d.y},${d.x})`);

        // Add circles to nodes
        nodes.append('circle')
            .attr('r', 5);

        // Add labels to nodes
        nodes.append('text')
            .attr('dx', 12)
            .attr('dy', 4)
            .text(d => d.data.name);
    } catch (error) {
        console.error('Error:', error);
    }
}

document.addEventListener('DOMContentLoaded', initializeTree);
