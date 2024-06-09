function _htmxRequest(data) {
    const { url } = data;
    const method = data.method || "GET";
    const target = data.target || "none";
    const swap = data.swap || "none";
    const values = data.values || {};

    return new Promise((resolve, reject) => {
        // Attach one-time event listeners for the response and error
        document.body.addEventListener('htmx:afterRequest', function(event) {
            const {response} = event.detail.xhr
            try {
                const data = JSON.parse(response);
                resolve({event, data});
            } catch (error) {
                resolve({event, data:response});
            }
        }, { once: true });


        document.body.addEventListener('htmx:responseError', function(event) {
            const {response} = event.detail.xhr
            try {
                const data = JSON.parse(response);
                reject({event, data});
            } catch (error) {
                reject({event, data:response});
            }
        }, { once: true });

        // Make the AJAX request using HTMX
        htmx.ajax(method, url, {
            target: target,
            swap: swap,
            values: values,
        });
    });
}

// Attach the function to the window object to make it globally accessible
window.htmxRequest = _htmxRequest;
