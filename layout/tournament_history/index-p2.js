(($) => {
  gsap.config({ nullTargetWarn: false, trialWarn: false });

  let startingAnimation = gsap
    .timeline({ paused: true });

  function Start() {
    startingAnimation.restart();
  }

  function getNumberWithOrdinal(n) {
    var s = ["th", "st", "nd", "rd"], v = n %100;
    return n+(s[(v - 20) % 10] || s[v] || s[0]);
  }

  var data = {};
  var oldData = {};

  async function Update() {
    oldData = data;
    data = await getData();
    if (!oldData.score ||
      JSON.stringify(data.score.history_sets) != JSON.stringify(oldData.score.history_sets)) {

      tournament_html = ""
      Object.values(data.score.history_sets["2"]).slice(0, 6).forEach((sets, s) => {
        tournament_html += `
        <div class="tournament${s+1} tournament_container">
          <div class="info">
            <div class="tournament_logo"></div>
            <div class="placement"></div>
            <div class="tournament_info">
              <div class="tournament_name"></div>
              <div class="event_name"></div>
            </div>
          </div>
        </div>`
        });
        $('.player2_content').html(tournament_html);

        Object.values(data.score.history_sets["2"]).slice(0, 6).forEach((tournament, s) => {
          SetInnerHtml($(`.player2_content .tournament${s+1} .info .tournament_info .tournament_name`), tournament.tournament_name);
          SetInnerHtml($(`.player2_content .tournament${s+1} .info .tournament_info .event_name`), tournament.event_name);
          SetInnerHtml($(`.player2_content .tournament${s+1} .info .tournament_logo`), 
          `
            <span class="logo" style="background-image: url('${tournament.tournament_picture}')"></span>
          `
          );
          SetInnerHtml($(`.player2_content .tournament${s+1} .info .placement`), getNumberWithOrdinal(tournament.placement));
          gsap.from($(`.tournament${s + 1}`), { y: +100, autoAlpha: 0, duration: 0.4 }, 0.5 + 0.3 * s);
      });
    }

    $(".text").each(function (e) {
      FitText($($(this)[0].parentNode));
    });

    $(".container div:has(>.text:empty)").css("margin-right", "0");
    $(".container div:not(:has(>.text:empty))").css("margin-right", "");
    $(".container div:has(>.text:empty)").css("margin-left", "0");
    $(".container div:not(:has(>.text:empty))").css("margin-left", "");
  }

  Update();
  $(window).on("load", () => {
    $("body").fadeTo(1, 1, async () => {
      Start();
      setInterval(Update, 500);
    });
  });
})(jQuery);
