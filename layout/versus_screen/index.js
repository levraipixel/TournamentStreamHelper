LoadEverything().then(() => {
  // Change this to the name of the assets pack you want to use
  // It's basically the folder name: user_data/games/game/ASSETPACK
  var ASSET_TO_USE = "full";

  // Change this to select wether to flip P2 character asset or not
  // Set it to true or false
  var FLIP_P2_ASSET = true;

  // Amount of zoom to use on the assets. Use 1 for 100%, 1.5 for 150%, etc.
  var zoom = 1;

  // Where to center character eyesights. [ 0.0 - 1.0 ]
  var EYESIGHT_CENTERING = { x: 0.5, y: 0.4 };

  let startingAnimation = gsap
    .timeline({ paused: true })
    .from(
      [".phase.container"],
      { duration: 0.8, opacity: "0", ease: "power2.inOut" },
      0
    )
    .from([".match"], { duration: 0.8, opacity: "0", ease: "power2.inOut" }, 0)
    .from(
      [".score_container"],
      { duration: 0.8, opacity: "0", ease: "power2.inOut" },
      0
    )
    .from(
      [".best_of.container"],
      { duration: 0.8, opacity: "0", ease: "power2.inOut" },
      0
    )
    .from([".vs"], { duration: 0.4, opacity: "0", scale: 4, ease: "out" }, 0.5)
    .from([".p1.container"], { duration: 1, x: "-100px", ease: "out" }, 0)
    .from([".p2.container"], { duration: 1, x: "100px", ease: "out" }, 0);

  async function Start() {
    startingAnimation.restart();
  }

  var lock = false;

  async function Update(event) {
    if (lock) return;
    lock = true;
    let data = event.data;
    let oldData = event.oldData;

    let isDoubles = Object.keys(data.score.team["1"].player).length == 2;

    if (!isDoubles) {
      const teams = Object.values(data.score.team);
      for (const [t, team] of teams.entries()) {
        const players = Object.values(team.player);
        for (const [p, player] of players.entries()) {
          SetInnerHtml(
            $(`.p${t + 1} .name`),
            `
              <span>
                  <div>
                    <span class='sponsor'>
                        ${player.team ? player.team : ""}
                    </span>
                    ${player.name}
                  </div>
                  ${team.losers ? "<span class='losers'>L</span>" : ""}
              </span>
            `
          );

          SetInnerHtml($(`.p${t + 1} .pronoun`), player.pronoun);

          SetInnerHtml(
            $(`.p${t + 1} > .sponsor_logo`),
            player.sponsor_logo
              ? `
                <div class='sponsor_logo' style='background-image: url(../../${player.sponsor_logo})'></div>
                `
              : ""
          );

          SetInnerHtml($(`.p${t + 1} .real_name`), `${player.real_name}`);

          SetInnerHtml(
            $(`.p${t + 1} .twitter`),
            `
              ${
                player.twitter
                  ? `
                  <div class="twitter_logo"></div>
                  ${player.twitter}
                  `
                  : ""
              }
          `
          );

          SetInnerHtml(
            $(`.p${t + 1} .flagcountry`),
            player.country.asset
              ? `
              <div>
                  <div class='flag' style='background-image: url(../../${player.country.asset});'>
                      <div class="flagname">${player.country.code}</div>
                  </div>
              </div>`
              : ""
          );

          SetInnerHtml(
            $(`.p${t + 1} .flagstate`),
            player.state.asset
              ? `
              <div>
                  <div class='flag' style='background-image: url(../../${player.state.asset});'>
                      <div class="flagname">${player.state.code}</div>
                  </div>
              </div>`
              : ""
          );

          let zIndexMultiplyier = 1;
          if (t == 1) zIndexMultiplyier = -1;

          await CharacterDisplay(
            $(`.p${t + 1}.character`),
            {
              source: `score.team.${t + 1}`,
              custom_center: [0.5, 0.4],
              custom_element: -2,
              anim_out: {
                x: zIndexMultiplyier * -800 + "px",
                z: 0,
                rotationY: zIndexMultiplyier * 15,
                stagger: 0.1,
              },
              anim_in: {
                duration: 0.4,
                x: zIndexMultiplyier * 20 + "px",
                z: 50 + "px",
                rotationY: zIndexMultiplyier * 15,
                ease: "in",
                autoAlpha: 1,
                stagger: 0.1,
              },
            },
            event
          );
        }
      }
    } else {
      Object.values(data.score.team).forEach((team, t) => {
        let teamName = "";

        if (!team.teamName || team.teamName == "") {
          let names = [];
          Object.values(team.player).forEach((player, p) => {
            if (player) {
              names.push(player.name);
            }
          });
          teamName = names.join(" / ");
        } else {
          teamName = team.teamName;
        }

        SetInnerHtml(
          $(`.p${t + 1} .name`),
          `
            <span>
                <div>
                  ${teamName}
                </div>
                ${team.losers ? "<span class='losers'>L</span>" : ""}
            </span>
          `
        );

        SetInnerHtml($(`.p${t + 1} > .sponsor_logo`), "");

        SetInnerHtml($(`.p${t + 1} .real_name`), ``);

        SetInnerHtml($(`.p${t + 1} .twitter`), ``);

        SetInnerHtml($(`.p${t + 1} .flagcountry`), "");

        SetInnerHtml($(`.p${t + 1} .flagstate`), "");

        CharacterDisplay($(`.p${t + 1}.character`), {
          source: `score.team.${t + 1}`,
          custom_center: [0.5, 0.4],
          custom_element: -2,
        });
      });
    }

    SetInnerHtml($(`.p1 .score`), String(data.score.team["1"].score));
    SetInnerHtml($(`.p2 .score`), String(data.score.team["2"].score));

    SetInnerHtml($(".tournament"), data.tournamentInfo.tournamentName);
    SetInnerHtml($(".match"), data.score.match);

    if (data.score.phase) {
      gsap.to($(".phase.container"), {
        autoAlpha: 1,
        overwrite: true,
        duration: 0.8,
      });

      SetInnerHtml(
        $(".phase:not(.container)"),
        data.score.phase ? `${data.score.phase}` : ""
      );
    } else {
      gsap.to($(".phase.container"), {
        autoAlpha: 0,
        overwrite: true,
        duration: 0.8,
      });
    }

    if (data.score.best_of_text) {
      gsap.to($(".best_of.container"), {
        opacity: 1,
        overwrite: true,
        duration: 0.8,
      });

      SetInnerHtml(
        $(".container .best_of"),
        data.score.best_of_text ? `${data.score.best_of_text}` : ""
      );
    } else {
      gsap.to($(".best_of.container"), {
        opacity: 0,
        overwrite: true,
        duration: 0.8,
      });
    }

    window.requestAnimationFrame(() => {
      if (gsap.globalTimeline.timeScale() == 0) {
        $(document).waitForImages(function () {
          $("body").fadeTo(1, 1, () => {
            Start();
            gsap.globalTimeline.timeScale(1);
          });
        });
      }
    });

    lock = false;
  }

  document.addEventListener("tsh_update", Update);
  gsap.globalTimeline.timeScale(0);
});
