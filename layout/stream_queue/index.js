LoadEverything().then(() => {
    /**
     * Wraps content in a .text element to emulate SetInnerHtml's behavior.
     */
    function wrap_text(txt){
        return `
            <div class = "text">${txt}</div>
        `
    }
    
    function online_avatar_html(player, t){
        return `
            <div class = "p${t}_avatar avatar_container"> 
                <span class="avatar" style="background-image: url('${player.online_avatar}')"></span>
            </div>
        `
    }

    async function team_html(set, t, isTeams){
        let team = set.team[""+t];
        let player = team.player["1"];
        return `
            <div class = "p${t} team">
                ${isTeams ? "" : online_avatar_html(player, t)}
                <div class = "name">
                    <div class = "tag">${ 
                        isTeams ? team.name : wrap_text(
                            `
                            <span class="sponsor">
                                ${player.team ? player.team : ""}
                            </span>
                            ${await Transcript(player.name)}
                            ${team.losers ? "<span class='losers'>L</span>" : ""}
                            `
                        )}
                    </div>
                    <div class = "extra">
                        <div class = "twitter"> ${ wrap_text((!isTeams && true) ?  `<span class="twitter_logo"></span>${String("Test_Twitter")}` : "") } </div> 
                        <div class = "pronoun"> ${ wrap_text((!isTeams && true) ?  String(player.pronoun) : "") } </div>
                        <div class = "seed"> ${wrap_text("Seed " + team.seed)} </div>
                    </div>
                </div>
                <div class = "flags">
                    ${ isTeams ? "" : 
                        (player.country.asset ? `<div class='flag' style='background-image: url(../../${player.country.asset.toLowerCase()})'></div>` : "") + 
                        (player.state.asset ? `<div class='flag' style='background-image: url(../../${player.state.asset.toLowerCase()})'></div>` : "")
                    }
                </div>
            </div>
        `
    }

    Update = async (event) => {
        let data = event.data;
        let oldData = event.oldData;

        if (
            !oldData.streamQueue ||
            JSON.stringify(data.streamQueue) !=
            JSON.stringify(oldData.score.streamQueue)
        ) {
            let stream = data.currentStream || tsh_settings.default_stream;
            let queue = data.streamQueue[stream];
            let html = ""
            for (const [s, set] of Object.values(queue).entries()){
                let isTeams = Object.keys(set.team["1"].player).length > 1;
                html += `
                    <div class="set${s + 1} set">
                        ${ await team_html(set, 1, isTeams) }
                        <div class = "vs_container">
                            <div class = "vs">VS</div>
                        </div>
                        ${ await team_html(set, 2, isTeams) }
                    </div>
                `;
            }
            console.log(html);
            $(".stream_queue_content").html(html);
        }
    }
})