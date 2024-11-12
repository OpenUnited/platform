import { BountyModal } from './BountyModal.js';
import { ChallengeFlow } from './ChallengeFlow.js';
import { FileUploadHandler } from './FileUploadHandler.js';

document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM Content Loaded - initializing components');
    new BountyModal();
    new ChallengeFlow();
    new FileUploadHandler();
    console.log('Components initialized');
}); 