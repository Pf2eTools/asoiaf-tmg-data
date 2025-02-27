"use strict";

class OBSControlPage {
    constructor() {
        this._data = {};
        this._statsIDMap = {};
        this._armies = {
            left: {
                faction: "",
                ids: []
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

    getExportArmyString (side) {
        const army = this._armies[side];
        if (army.faction === "" && army.ids.length === 0) return "";
        let out = "";

        if (army.faction !== "") out += `Faction: ${Parser.renderFaction(army.faction, true)}\n`;
        else out += "Faction: None\n";

        const commanderId = army.ids.find(id => this._data[id].statistics.commander);
        if (commanderId !== undefined) out += `Commander: ${this._data[commanderId]._fullName}\n`;
        else out += "Commander: None\n";

        let unitsPart = ""
        for (const id of army.ids) {
            const ent = this._data[id];
            if (ent.__prop === "units") unitsPart += ` • ${ent._fullName} (${ent.statistics.cost})\n`;
            else if (ent.__prop === "attachments" && !ent.statistics.enemy) unitsPart += `     ${ent._fullName} (${ent.statistics.cost})\n`;
        }
        if (unitsPart !== "") out += "\nCombat Units\n" + unitsPart
        else out += "\nNo Combat Units Selected\n"

        let ncuPart = ""
        for (const id of army.ids) {
            const ent = this._data[id];
            if (ent.__prop === "ncus") ncuPart += ` • ${ent._fullName} (${ent.statistics.cost})\n`;
        }
        if (ncuPart !== "") out += "\nNCUs\n" + ncuPart
        else out += "\nNo NCUs Selected\n"

        let enemyPart = ""
        for (const id of army.ids) {
            const ent = this._data[id];
            if (ent.__prop === "attachments" && ent.statistics.enemy) enemyPart += ` • ${ent._fullName} (${ent.statistics.cost})\n`;
        }
        if (enemyPart !== "") out += "\nEnemy Attachments\n" + enemyPart

        out += `\nImport String\n${army.faction};${army.ids.join(",")}`

        return out
    }

    _onClickImport() {
        const {$modalInner} = UiUtil.getShowModal({
            title: "Import Army",
            isUncappedHeight: true,
        });

        const $getImportSideBtn = (side, handler) => {
            return $(`<button class="btn btn-sm btn-info ml-2">Import ${side.uppercaseFirst()}</button>`).on("click", async () => {
                await handler(side);
            })
        }

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
            if (this._armies[side].faction === "brotherhoodwithoutbanners") this._armies[side].faction = "brotherhood";
            this._armies[side].ids = statsJson.idArray.map(id => Parser._parse_bToA(this._statsIDMap, String(id)));

            this.renderArmy(side);
        }

        const $iptString = $(`<input class="form-control input-sm w-100" type="text">`)
        const importString = async (side) => {
            const val = $iptString.val();
            if (typeof val != "string" || val === "") return;

            const [faction, ids] = val.trim().split(";");
            this._armies[side].faction = faction.toLowerCase().replaceAll(/\W/g, "");
            this._armies[side].ids = ids.split(",");

            this.renderArmy(side);
        }

        const $iptDraftmancer = $(`<textarea class="form-control input-sm w-100" rows="1" style="resize: none">`)
        const importDraftmancer = async (side) => {
            this._armies[side].faction = "";
            this._armies[side].ids = [];

            const val = $iptDraftmancer.val();
            if (typeof val != "string" || val === "") return;

            const [listContent, sideBarContent] = val.trim().split("\n\n");
            const listItems = listContent.split("\n").map(it => it.replace("1 ", ""));

            for (const itemId of listItems) {
                if (/Basedeck/.test(itemId)) {
                    this._armies[side].faction = itemId.replace("Basedeck", "");
                } else {
                    this._armies[side].ids.push(itemId);
                }
            }

            this.renderArmy(side);
        }


        const $getExportSideBtn = (side) => {
            return $(`<button class="btn btn-sm btn-info ml-2">Export ${side.uppercaseFirst()}</button>`).on("click", async () => {
                const armyString = this.getExportArmyString(side);
                if (armyString === "") return;
                await navigator.clipboard.writeText(armyString);
            })
        }

        $modalInner.append($$`
           <h4>ASOIAF-STATS</h4>
           <div class="ve-flex">
                ${$iptStats}
                ${$getImportSideBtn("left", importStats)}
                ${$getImportSideBtn("right", importStats)}
           </div>
           
           <h4 class="mt-3">CSV</h4>
           <p>Use this format: <span class="code">faction;id1,id2,id3,...</span></p>
           <div class="ve-flex">
                ${$iptString}
                ${$getImportSideBtn("left", importString)}
                ${$getImportSideBtn("right", importString)}
           </div>

           <h4 class="mt-3">DRAFTMANCER</h4>
           <p class="m-0">Build your list in draftmancer. Make sure to add items in the correct order:</p>
           <p class="m-0">First, your tactics deck. Then, add units and their attachments. Finally add NCUs.</p>
           <p>When you are ready to import, click <span class="code">Export > Card Names</span> and paste here.</p>
           <div class="ve-flex">
                ${$iptDraftmancer}
                ${$getImportSideBtn("left", importDraftmancer)}
                ${$getImportSideBtn("right", importDraftmancer)}
           </div>

            <h4>Copy to Clipboard</h4>
            <div class="ve-flex">
                ${$getExportSideBtn("left")}
                ${$getExportSideBtn("right")}
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
        const marginLeft = unit.__prop === "units" || unit.__prop === "ncus" ? "0px" : "40px";
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
