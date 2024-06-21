// ==UserScript==
// @name         obs-overlay-client
// @namespace    http://tampermonkey.net/
// @version      2024-06-19
// @description  try to take over the world!
// @author       You
// @match        https://pf2etools.github.io/asoiaf-tmg-data/web/song.html
// @match        *://localhost/*/web/song.html
// @icon         https://www.google.com/s2/favicons?sz=64&domain=github.io
// @grant        none
// ==/UserScript==

OBS_WS_PORT = 9999;
(function() {
    'use strict';

    function injectButton({styles, text, getMessage}) {
        const $wrpBtns = $("#btn-book").parent();
        window.$$`<button class="btn btn-xs m-1 ${styles}">${text}</button>`.click(() => {
            const socket = new WebSocket(`ws://localhost:${OBS_WS_PORT}`);
            socket.addEventListener("open", () => {
                socket.send(getMessage());
                socket.close();
            });
        }).appendTo($wrpBtns);
    }

    // Only inject if the socket is up
    const socket = new WebSocket(`ws://localhost:${OBS_WS_PORT}`);
    socket.addEventListener("open", () => {
        injectButton({
            styles: "btn-default",
            text: "Send to OBS",
            getMessage: () => "SHOW;" + songPage._lastRender.entity._img.face,
        });
        // injectButton({
        //     styles: "btn-info",
        //     text: "Send list to OBS",
        //     getMessage: () => "SHOW;" + songPage._sublistManager.sublistItems.map(it => it.data.entity._img.face).join(";"),
        // });
        injectButton({
            styles: "btn-danger",
            text: "Clear OBS",
            getMessage: () => "CLEAR;",
        });
    });
})();
