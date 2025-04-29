async function gen_pdf(languages, factions, versions) {
    console.log("This might take a while...")
    for (const lang of languages) {
        for (const faction of factions) {
            for (const version of versions) {
                for (const size of ["lg", "sm"]) {
                    await songPage._sublistManager.pDoSublistRemoveAll()
                    const name = `${lang}-${faction}-${size}-${version}`;
                    console.log(`Generating ${name}.pdf ...`)
                    for (const entity of songPage._dataList) {
                        if (entity.__prop !== "units" && size === "lg") continue;
                        if (entity.__prop === "units" && size === "sm") continue;
                        if (entity.lang !== lang) continue;
                        if (entity.statistics.faction !== faction) continue;
                        if (version === "s06" && entity.statistics.version !== "S06") continue;
                        let addCount;
                        if (entity.id === "10303") addCount = 4; // raiders
                        else if (entity.id === "50201") addCount = 3; // crannog poison
                        else if (entity.__prop === "tactics") addCount = 2;
                        else if (entity.__prop === "ncus" || entity.__prop === "specials") addCount = 1;
                        else if (entity._fCharacter.includes("Is a Character")) addCount = 1;
                        else addCount = 2;
                        await songPage._sublistManager.pDoSublistAdd({entity, addCount})
                    }
                    songPage._bookView._pdfMargin = 1;
                    songPage._bookView._pdfPadding = 0;
                    songPage._bookView._pdfCuttingGuide = "1";
                    songPage._bookView._printBackside = "1";
                    songPage._bookView._pdfFile = new jspdf.jsPDF();
                    songPage._bookView._pdfFile.deletePage(1);
                    await songPage._bookView._preparePdf_Singletons();
                    const blob = songPage._bookView._pdfFile.output("blob");
                    const filename = `${name}.pdf`;
                    DataUtil.userDownloadBlob(filename, blob);
                }
            }
        }
    }
}

gen_pdf(["en", "de"], Parser.FACTIONS, ["all", "s06"]);
