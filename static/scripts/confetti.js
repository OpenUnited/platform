const publishBtnOpen = document.querySelector("#publish-btn button");
const modalPublish = document.querySelector(".modal-publish");

if (publishBtnOpen) {
  publishBtnOpen.addEventListener("click", () => {
    modalPublish.classList.remove("hidden");

    (async () => {
      const canvas = document.getElementById("confetti-boom");
    
      // you should  only initialize a canvas once, so save this function
      // we'll save it to the canvas itself for the purpose of this demo
      canvas.confetti =
        canvas.confetti || (await confetti.create(canvas, { resize: true }));
    
      canvas.confetti({
        spread: 70,
        origin: { y: 1.2 },
      });

      const duration = 5 * 1000,
            animationEnd = Date.now() + duration,
            defaults = { startVelocity: 30, spread: 360, ticks: 60, zIndex: 0 };

          function randomInRange(min, max) {
            return Math.random() * (max - min) + min;
          }

          const interval = setInterval(function() {
            const timeLeft = animationEnd - Date.now();

            if (timeLeft <= 0) {
              window.location.href = "/";
              return
            }

            const particleCount = 50 * (timeLeft / duration);

            // since particles fall down, start a bit higher than random
            confetti(
              Object.assign({}, defaults, {
                particleCount,
                origin: { x: randomInRange(0.1, 0.3), y: Math.random() - 0.2 },
              })
            );
            confetti(
              Object.assign({}, defaults, {
                particleCount,
                origin: { x: randomInRange(0.7, 0.9), y: Math.random() - 0.2 },
              })
            );
        }, 250);
    })();
  });
}

