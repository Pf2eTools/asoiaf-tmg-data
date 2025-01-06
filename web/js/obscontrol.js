"use strict";

class OBSControlPage {
    constructor() {
        this._data = {};
        this._statsIDMap = {};
        this._armies = {
            left: {
                faction: "",
                ids: [
                ]
            },
            right: {
                faction: "",
                ids: []
            },
        }
    }

    async pOnLoad() {
        const rawData = await DataUtil.song.pLoadSingleSource("en");
        Object.values(rawData).forEach(items => items.forEach(it => this._data[it.id] = it));
        $(`#btn-import`).on("click", () => this._onClickImport());
        $(`#btn-day-night`).on("click", () => $(`html`).toggleClass("night-mode"));
        $(`body`).on("click", evt => {
            if (evt.target.nodeName === "DIV" && evt.target.onclick == null) this._sendMessageToOBS("CLEAR;");
        });

        this._statsIDMap = await DataUtil._loadJson(`${DataUtil.song._BASEDIR}/warcouncil-to-asoiaf-stats.json`);
    }

    _onClickImport() {
        const {$modalInner} = UiUtil.getShowModal({
            title: "Import Army"
        });

        const $iptStats = $(`<input class="form-control input-sm w-100" type="text">`)
        const importStats = async (side) => {
            const listID = $iptStats.val();
            if (typeof listID != "string" || listID === "" || !listID.startsWith("PLAYER")) return;

            const statsJson = await DataUtil._pLoad({
                url: `https://51jadhwyqc.execute-api.eu-west-2.amazonaws.com/prod/tts-list-2?listId=${listID}`,
                id: listID,
                isBustCache: true
            });
            if (statsJson == null || statsJson.faction == null || statsJson.idArray == null) return;

            this._armies[side].faction = statsJson.faction.name.toLowerCase().replaceAll(/\W/g, "");
            this._armies[side].ids = statsJson.idArray.map(id => Parser._parse_bToA(this._statsIDMap, String(id)));

            this.renderArmy(side);
        }
        const $btnImportStatsLeft = $(`<button class="btn btn-sm btn-info ml-2">Import Left</button>`).on("click", async () => {
            await importStats("left");
        });
        const $btnImportStatsRight = $(`<button class="btn btn-sm btn-info ml-2">Import Right</button>`).on("click", async () => {
            await importStats("right");
        });

        const $iptString = $(`<input class="form-control input-sm w-100" type="text">`)
        const importString = async (side) => {
            const val = $iptString.val();
            if (typeof val != "string" || val === "") return;

            const [faction, ids] = val.split(";");
            this._armies[side].faction = faction.toLowerCase().replaceAll(/\W/g, "");
            this._armies[side].ids = ids.split(",");

            this.renderArmy(side);
        }
        const $btnImportStringLeft = $(`<button class="btn btn-sm btn-info ml-2">Import Left</button>`).on("click", async () => {
            await importString("left");
        });
        const $btnImportStringRight = $(`<button class="btn btn-sm btn-info ml-2">Import Right</button>`).on("click", async () => {
            await importString("right");
        });

        $modalInner.append($$`
           <h4>ASOIAF-STATS</h4>
           <div class="ve-flex">
                ${$iptStats}
                ${$btnImportStatsLeft}
                ${$btnImportStatsRight}
           </div>
           
           <h4 class="mt-3">CSV</h4>
           <p>Use this format: <span class="code">faction;id1,id2,id3,...</span></p>
           <div class="ve-flex">
                ${$iptString}
                ${$btnImportStringLeft}
                ${$btnImportStringRight}
           </div>`);
    }

    renderArmy(side) {
        if (side !== "left" && side !== "right") return;

        const faction = this._armies[side].faction;

        const $wrpArmy = $(`#wrp-army--${side}`).empty();
        for (const uid of this._armies[side].ids) {
            $wrpArmy.append(this._getRenderedUnit(uid))
        }
        const $wrpHead = $(`#wrp-head--${side}`).empty();
        const cmdrId = this._armies[side].ids.find(id => this._data[id].statistics.commander);
        $wrpHead.append($(`<h2>${Parser.renderFaction(faction)} - ${this._data[cmdrId].name}</h2>`))

        const $wrpTactics = $(`#wrp-tactics--${side}`).empty();
        const baseDeck = Object.values(this._data).filter(it => {
            const remove = (this._data[cmdrId].tactics.remove || []).map(n => n.toUpperCase());
            if (it.__prop !== "tactics") return false;
            if (it.statistics.faction !== faction) return false;
            if (it.statistics.commander_id != null) return false;
            if (remove.includes("ALL")) return false;
            if (remove.includes(it.name.toUpperCase())) return false;
            //
            return true;
        });
        for (const card of [...Object.keys(this._data[cmdrId].tactics.cards).map(id => this._data[id]), ...baseDeck]) {
            $wrpTactics.append(this._getRenderedTactics(card))
        }
    }

    _getRenderedUnit(uid) {
        const unit = this._data[uid];
        const hoverStr = Renderer.get()._renderLink_getHoverString({
            href: {
                type: "internal",
                path: UrlUtil.PG_SONG,
                hash: UrlUtil.URL_TO_HASH_BUILDER[UrlUtil.PG_SONG](unit),
                hashPreEncoded: true,
                hover: {page: UrlUtil.PG_SONG, source: "en"}
            }
        });
        const marginLeft = unit.__prop === "units" || unit.__prop === "ncus" ? "0px": "40px";
        return $$`<div ${hoverStr} class="ve-flex card" style="margin-left: ${marginLeft};">
					<img src="../portraits/square/${uid}.jpg" alt="?" class="m-0 unit-img">
					<p class="card-p">
					    <span class="unit-name">${unit.name}</span>
					    <span class="unit-name unit-sub-name">${unit.subname || ""}</span>
					</p>
				</div>`.click(() => this._sendMessageToOBS(`SHOW;${unit._img.face}`));
    }

    _getRenderedTactics(card) {
        const hoverStr = Renderer.get()._renderLink_getHoverString({
            href: {
                type: "internal",
                path: UrlUtil.PG_SONG,
                hash: UrlUtil.URL_TO_HASH_BUILDER[UrlUtil.PG_SONG](card),
                hashPreEncoded: true,
                hover: {page: UrlUtil.PG_SONG, source: "en"}
            }
        });

        const imgSrc = card.statistics.commander_id ? `../portraits/square/${card.statistics.commander_id}.jpg` : `../assets/warcouncil/${card.statistics.faction}/crest.png`

        return $$`<div ${hoverStr} class="ve-flex card">
					<img src="${imgSrc}" alt="?" class="m-0 unit-img">
					<p class="card-p">
					    <span class="unit-name">${card.name}</span>
					</p>
				</div>`.click(() => this._sendMessageToOBS(`SHOW;${card._img.face}`));
    }

    _sendMessageToOBS(message) {
        const socket = new WebSocket(`ws://localhost:9999`);
        socket.addEventListener("open", () => {
            socket.send(message);
            socket.close();
        });
    }
}

const controlPage = new OBSControlPage();
window.addEventListener("load", () => controlPage.pOnLoad());
