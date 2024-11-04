function handleBountyClaimCancel(claimId, bountyTitle) {
    if (!confirm(`Are you sure to cancel the following claim? ${bountyTitle}`)) {
        return;
    }

    fetch(`/portal/bounty-claims/${claimId}/cancel/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => {
        if (response.ok) {
            window.location.reload();
        }
    });
}

function handleBountyClaim(claimId, action, personName) {
    const confirmMessage = action === 'accept' 
        ? `Accepting this bounty claim request from ${personName} means that the other bounty claim requests will be rejected. Are you sure to continue?`
        : `Are you sure to reject this bounty request from ${personName}?`;

    if (!confirm(confirmMessage)) {
        return;
    }

    fetch(`/portal/bounty-claims/${claimId}/${action}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => {
        if (response.ok) {
            window.location.reload();
        }
    });
} 