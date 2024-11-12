import { BountyModal } from './BountyModal.js';
import { ChallengeFlow } from './ChallengeFlow.js';
import { FileUploadHandler } from './FileUploadHandler.js';

document.addEventListener('DOMContentLoaded', () => {
    new BountyModal();
    new ChallengeFlow();
    new FileUploadHandler();
}); 