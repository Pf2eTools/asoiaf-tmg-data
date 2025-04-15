"use strict";

class OBSControlPage {
    constructor() {
        this._socketPort = 9999;
        this._socket = null;
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
        this._state = {
            firstPlayer: "left",
            round: 1,
            name: {
                left: "",
                right: "",
            },
            vp: {
                left: 0,
                right: 0,
            },
            cards: ["", "", "", ""]
        }
        this._slot = 0;
        this._$slotBtns = [null, null, null, null];
        this._$trashBtns = [null, null, null, null];

        this._syncStateDebounced = MiscUtil.debounce(this._syncState.bind(this), 200);
    }

    _connectSocket() {
        if (this._socket) this._socket.close();
        const port = isNaN(Number(this._socketPort)) ? 9999 : Number(this._socketPort);
        this._socket = new WebSocket(`ws://localhost:${port}`);
        this._socket.addEventListener("open", () => {
            console.log("Websocket Connected!")
            $("#socket-status").html("Connected").toggleClass("btn-danger", false);
            $("#btn-sock-connect").html("Reconnect");
        });

        this._socket.addEventListener("close", () => {
            console.log("Websocket Closed!")
            $("#socket-status").html("Not Connected").toggleClass("btn-danger", true);
            $("#btn-sock-connect").html("Connect");
        });
    }

    _swapFirstPlayer() {
        this._state.firstPlayer = this._state.firstPlayer === "left" ? "right" : "left"
        const html = this._state.firstPlayer === "left"
            ? `<span class="glyphicon glyphicon-arrow-left mx-1"></span>First Player`
            : `First Player<span class="glyphicon glyphicon-arrow-right mx-1"></span>`
        $(`#btn-first-player`).html(html);

        this._syncStateDebounced();
    }

    async pOnLoad() {
        const rawData = await DataUtil.song.pLoadSingleSource("en");
        Object.values(rawData).forEach(items => items.forEach(it => this._data[it.id] = it));
        $(`#btn-import`).on("click", () => this._onClickImport());
        $(`#btn-day-night`).on("click", () => styleSwitcher.cycleDayNightMode());

        const $iptPort = $(`#ipt-sock-port`).on("change", () => this._socketPort = Number($iptPort.val()));
        $(`#btn-sock-connect`).on("click", () => this._connectSocket());

        this._socketPort = Number($iptPort.val());
        this._connectSocket();

        $(".btn-group").children().each((ix, btn) => $(btn).on("click", () => this._setActiveSlot(ix)));
        $(`.btn-lg.btn-danger`).on("click", () => {
            [0, 1, 2, 3].forEach(n => this._clearSlot(n));
            this._setActiveSlot(0);
        });

        $(`#btn-first-player`).on("click", () => this._swapFirstPlayer());
        const $iptRound = $(`#ipt-round`).on("change", () => {
            this._state.round = Number($iptRound.val());
            this._swapFirstPlayer();
        });

        $("#ipt-name-left").on("change", (e) => {
            this._state.name.left = e.target.value;
            this._syncStateDebounced();
        });
        $("#ipt-name-right").on("change", (e) => {
            this._state.name.right = e.target.value;
            this._syncStateDebounced();
        });
        $("#ipt-vp-left").on("change", (e) => {
            this._state.vp.left = Number(e.target.value);
            this._syncStateDebounced();
        });
        $("#ipt-vp-right").on("change", (e) => {
            this._state.vp.right = Number(e.target.value);
            this._syncStateDebounced();
        });

        this._statsIDMap = await DataUtil._loadJson(`${DataUtil.song._BASEDIR}/warcouncil-to-asoiaf-stats.json`);
    }

    getExportArmyString(side) {
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

    _getRenderedSongEntity(uid) {
        const entity = this._data[uid];
        const hoverStr = Renderer.get()._renderLink_getHoverString({
            href: {
                type: "internal",
                path: UrlUtil.PG_SONG,
                hash: UrlUtil.URL_TO_HASH_BUILDER[UrlUtil.PG_SONG](entity),
                hashPreEncoded: true,
                hover: {page: UrlUtil.PG_SONG, source: "en"}
            }
        });
        const marginLeft = entity.__prop === "attachments" ? "40px" : "0px";

        const $btnSlot = $(`<button class="btn btn-default ml-auto mr-1 hidden">1</button>`)
        const $btnTrash = $(`<button class="btn btn-danger hidden"><span class="glyphicon glyphicon-trash"></span></button>`).on("click", evt => {
            const slot = Number($btnSlot.html()) - 1;
            this._clearSlot(slot);
        });

        const imgSrc = entity.__prop === "tactics"
            ? entity.statistics.commander_id ? `../portraits/square/${entity.statistics.commander_id}.jpg` : `../assets/warcouncil/${entity.statistics.faction}/crest.png`
            : `../portraits/square/${uid}.jpg`;

        const $addArea = $(`<img ${hoverStr} src="${imgSrc}" alt="?" class="m-0 unit-img">
                            <p class="card-p">
                                <span class="unit-name">${entity.name}</span>
                                <span class="unit-name unit-sub-name">${entity.subname || ""}</span>
                            </p>`
        ).on("click", evt => {
            evt.stopPropagation();
            evt.preventDefault();
            this._addCardToSlot(entity, $btnSlot, $btnTrash);
        });

        return $$`<div class="ve-flex card" style="margin-left: ${marginLeft};">
					${$addArea}
					${$btnSlot}
					${$btnTrash}
				</div>`;
    }

    renderArmy(side) {
        if (side !== "left" && side !== "right") return;

        const faction = this._armies[side].faction;

        const $wrpArmy = $(`#wrp-army--${side}`).empty();
        for (const uid of this._armies[side].ids) {
            $wrpArmy.append(this._getRenderedSongEntity(uid));
        }
        const $wrpHead = $(`#wrp-head--${side}`);
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
            $wrpTactics.append(this._getRenderedSongEntity(card.id));
        }
    }

    _setActiveSlot(slot) {
        this._slot = slot;
        $(".btn-group").children().each((ix, btn) => {
            $(btn).toggleClass("active", this._slot === ix);
        });
    }

    _addCardToSlot (card, $btnSlot, $btnTrash) {
        const slot = this._slot;

        if (this._state.cards[slot] !== "") this._clearSlot(slot);
        const ixExisting = this._$slotBtns.findIndex(btn => btn === $btnSlot);
        if (ixExisting !== -1) this._clearSlot(ixExisting);

        $btnSlot.html(slot + 1);
        $btnSlot.toggleClass("hidden", false);
        $btnTrash.toggleClass("hidden", false);

        this._$trashBtns[slot] = $btnTrash;
        this._$slotBtns[slot] = $btnSlot;
        this._state.cards[slot] = `${card.statistics.faction}/${card.id}`;

        let nextSlot = this._state.cards.slice(slot).findIndex(it => it === "") + slot;
        if (nextSlot < slot && this._state.cards.includes("")) nextSlot = this._state.cards.findIndex(it => it === "");
        else if (nextSlot < slot) nextSlot = (slot + 1) % 4;
        this._setActiveSlot(nextSlot);

        this._syncStateDebounced();
    }

    _clearSlot(slot) {
        if (!this._state.cards.includes("")) this._setActiveSlot(slot);

        const $btnSlot = this._$slotBtns[slot];
        const $btnTrash = this._$trashBtns[slot];
        if ($btnSlot !== null) $btnSlot.toggleClass("hidden", true);
        if ($btnTrash !== null) $btnTrash.toggleClass("hidden", true);
        this._$trashBtns[slot] = null;
        this._$slotBtns[slot] = null;
        this._state.cards[slot] = "";

        this._syncStateDebounced();
    }

    _sendMessageToOBS(message) {
        if (this._socket && this._socket.readyState === 1) {
            console.log(`Senging Message to OBS:\n${message}`)
            this._socket.send(message);
        } else {
            this._connectSocket();
            this._socket.addEventListener("open", () => {
                console.log(`Senging Message to OBS:\n${message}`)
                this._socket.send(message);
            });
        }
    }

    _syncState() {
        const parts = ["SYNC"];
        parts.push(this._state.firstPlayer === "left" ? "0" : "1");
        parts.push(this._state.round);
        parts.push(`${this._state.name.left},${this._state.name.right}`);
        parts.push(`${this._state.vp.left},${this._state.vp.right}`);
        parts.push(this._state.cards.join(","));
        this._sendMessageToOBS(parts.join(";"));
    }

}

const controlPage = new OBSControlPage();
window.addEventListener("load", () => controlPage.pOnLoad());
