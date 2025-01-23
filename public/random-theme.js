(function() {
    // Some sample purple hues
    const purples = [
      '#4B0082', // indigo
      '#6A0DAD',
      '#7F3FBF',
      '#8A2BE2',
      '#9370DB',
      '#663399'
    ];
    // pick random
    const randomColor = purples[Math.floor(Math.random() * purples.length)];
    document.body.style.backgroundColor = randomColor;
  })();
  