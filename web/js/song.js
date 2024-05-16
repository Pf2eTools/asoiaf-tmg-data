"use strict";

class SongSublistManager extends SublistManager {

	constructor() {
		super({
			isSublistItemsCountable: true,
			shiftCountAddSubtract: 2,
		});
	}
	static get _ROW_TEMPLATE () {
		return [
			new SublistCellTemplate({
				name: "Name",
				css: "bold ve-col-6-2 pl-0",
				colStyle: "",
			}),
			new SublistCellTemplate({
				name: "Faction",
				css: "ve-col-2-2 text-center",
				colStyle: "text-right",
			}),
			new SublistCellTemplate({
				name: "Type",
				css: "ve-col-2-2 text-center",
				colStyle: "text-right",
			}),
			new SublistCellTemplate({
				name: "#",
				css: "ve-text-center ve-grow pr-0",
				colStyle: "text-center",
			}),
		];
	}

	pGetSublistItem (obj, hash, {count = 1} = {}) {
		const faction = Parser.renderFaction(obj.statistics.faction);
		const type = Parser.renderProp(obj.__prop);

		const cellsText = [
			obj.name,
			faction,
			type,
		];

		const $dispCount = $(`<span class="ve-text-center ve-grow pr-0">${count}</span>`);
		const $ele = $$`<div class="lst__row lst__row--sublist ve-flex-col">
			<a href="#${UrlUtil.autoEncodeHash(obj)}" title="${obj.name}" class="lst--border lst__row-inner">
				${this.constructor._getRowCellsHtml({values: cellsText, templates: this.constructor._ROW_TEMPLATE.slice(0, 3)})}
				${$dispCount}
			</a>
		</div>`.contextmenu(evt => this._handleSublistItemContextMenu(evt, listItem))
			.click(evt => this._listSub.doSelect(listItem, evt));

		const listItem = new ListItem(
			hash,
			$ele,
			obj.name,
			{
				hash,
				faction,
				type,
			},
			{
				count,
				$elesCount: [$dispCount],
				entity: obj,
				mdRow: [...cellsText],
			},
		);
		return listItem;
	}
}

class SongPageBookView extends ListPageBookView {
	static _PRINT_MODE_K = "bookViewMode";
	static _PDF_MARGIN_K = "pdfMargin";
	static _PDF_PADDING_K = "pdfPadding";
	static _PDF_CUTTING_GUIDE = "cuttingGuide";
	constructor (opts) {
		super({
			pageTitle: "Print View",
			namePlural: "cards",
			...opts,
		});

		this._printMode = null;
		this._pdfMargin = null;
		this._pdfPadding = null;
		this._pdfCuttingGuide = null;
		this._$wrpContent = null;

		// Aware
		this._pdfFile = null;
		this._btnOpenPdf = null;
		this._progressPdf = null;
	}

	_getSorted (a, b) {
		return SortUtil.ascSortLowerProp("id", a, b);
	}

	async _$pGetWrpControls ({$wrpContent}) {
		const $wrp = $(`<div class="w-100 ve-flex-col no-shrink no-print"></div>`);

		$wrp.addClass("px-2 mt-2 bb-1p pb-1");

		const $wrpPrint = $$`<div class="w-100 ve-flex"></div>`.appendTo($wrp);

		this._printMode = StorageUtil.syncGetForPage(SongPageBookView._PRINT_MODE_K);
		this._pdfMargin = StorageUtil.syncGetForPage(SongPageBookView._PDF_MARGIN_K);
		this._pdfPadding = StorageUtil.syncGetForPage(SongPageBookView._PDF_PADDING_K);
		this._pdfCuttingGuide = StorageUtil.syncGetForPage(SongPageBookView._PDF_CUTTING_GUIDE);
		if (this._printMode != null) this._printMode = `${this._printMode}`;

		const $selMode = $(`<select class="form-control input-sm">
			<option value="0">A4 Page</option>
			<option value="1">Singletons</option>
		</select>`)
			.change(() => {
				if (!this._bookViewToShow.length && Hist.lastLoadedId != null) return;

				const val = $selMode.val();
				this._printMode = val;
				if (val === "0") this._renderSingletons();
				else if (val === "1") this._renderSingletons();

				StorageUtil.syncSetForPage(SongPageBookView._PRINT_MODE_K, val);
			});
		if (this._printMode != null) $selMode.val(this._printMode);
		else this._printMode = $selMode.val();

		const $iptMargin = $(`<input class="form-control input-sm" style="max-width: 60px" type="number" min="0" max="40" maxlength="2" value="0">`)
			.change(() => {
				const val = $iptMargin.val();
				this._pdfMargin = val;
				StorageUtil.syncSetForPage(SongPageBookView._PDF_MARGIN_K, val);
			});
		if (this._pdfMargin != null) $iptMargin.val(this._pdfMargin);
		else this._pdfMargin = $iptMargin.val();

		const $iptPadding = $(`<input class="form-control input-sm" style="max-width: 60px" type="number" min="0" max="20" maxlength="2" value="0">`)
			.change(() => {
				const val = $iptPadding.val();
				this._pdfPadding = val;
				StorageUtil.syncSetForPage(SongPageBookView._PDF_PADDING_K, val);
			});
		if (this._pdfPadding != null) $iptPadding.val(this._pdfPadding);
		else this._pdfPadding = $iptPadding.val();

		const $selCuttingGuide = $(`<select class="form-control input-sm">
			<option value="1">Yes</option>
			<option value="0">No</option>
		</select>`)
			.change(() => {
				const val = $selCuttingGuide.val();
				this._pdfCuttingGuide = val;
				StorageUtil.syncSetForPage(SongPageBookView._PDF_CUTTING_GUIDE, val);
			});
		if (this._pdfCuttingGuide != null) $selCuttingGuide.val(this._pdfCuttingGuide);
		else this._pdfCuttingGuide = $selCuttingGuide.val();

		$$`<div class="ve-flex-vh-center ml-3">
			<div class="mr-2 no-wrap">Mode:</div>${$selMode}
			<div class="mr-2 ml-4 no-wrap"><span class="help" title='Space around each page'>Margin</span> (<span class="help" title='1mm = 0.04"'>mm</span>):</div>${$iptMargin}
			<div class="mr-2 ml-4 no-wrap">Cutting Guides</div>${$selCuttingGuide}
			<div class="mr-2 ml-4 no-wrap"><span class="help" title='Spacing between cards'>Padding</span> (<span class="help" title='1mm = 0.04"'>mm</span>):</div>${$iptPadding}
		</div>`.appendTo($wrpPrint);

		return {$wrp, $wrpPrint};
	}

	async _$pGetWrpFooter () {
		const $displayProgress = $(`<div class="page__disp-download-progress-bar"/>`);
		this._$displayPercent = $(`<div class="page__disp-download-progress-text page__disp-download-progress-text--wide ve-flex-vh-center bold">Generating... 0%</div>`);

		const $wrapBar = $$`<div class="page__wrp-download-bar w-100 relative mr-2">${$displayProgress}${this._$displayPercent}</div>`;
		const $wrapOuter = $$`<div class="page__wrp-download" style="position: unset; display: none">
			${$wrapBar}
		</div>`;

		this._progressPdf = {$wrapOuter, $wrapBar, $displayProgress};
		const disabled = !this._bookViewToShow.length && Hist.lastLoadedId != null ? "disabled" : ""
		this._btnOpenPdf = $(`<button class="btn btn-info m-3 ${disabled}" ${disabled}>Download PDF</button>`).click(() => this._preparePdf());
		return $$`<div class="w-100 ve-flex-vh-center no-shrink no-print">${this._btnOpenPdf}${$wrapOuter}</div>`;
	}

	_renderEnt_Singleton ({stack, ent}) {
		const src = ent._img.face;
		stack.push(`<img class="m-1 bkmv__img" src="${src}" alt="?">`);
	}

	_renderSingletons () {
		const stack = [];
		this._bookViewToShow.forEach(ent => this._renderEnt_Singleton({stack, ent}));
		this._$wrpContent.empty().append(stack.join(""));
		return {isAnyEntityRendered: !!this._bookViewToShow.length};
	}

	_renderFillPage () {
		const stack = [];
		this._bookViewToShow.forEach(ent => this._renderEnt_Singleton({stack, ent}));
		this._$wrpContent.empty().append(stack.join(""));
		return {isAnyEntityRendered: !!this._bookViewToShow.length};
	}

	_renderNoneSelected () {
		const stack = [];
		stack.push(`<div class="w-100 h-100 no-breaks">`);
		this._renderEnt_Singleton({stack, ent: this._fnGetEntLastLoaded()});
		stack.push(`</div>`);
		this._$wrpContent.empty().append(stack.join(""));
		return {isAnyEntityRendered: false};
	}

	_renderEntities () {
		if (!this._bookViewToShow.length && Hist.lastLoadedId != null) return this._renderNoneSelected();
		else if (this._printMode === "1") return this._renderSingletons();
		else return this._renderFillPage();
	}

	async _preparePdf_Singletons () {
		const margin = Number(this._pdfMargin);
		const items = this._sublistManager.sublistItems.sort((a, b) => SortUtil.ascSortLower(a.ix, b.ix));
		let completed = 0;

		for (const item of items) {
			const ent = item.data.entity;
			const count = item.data.count;
			const src = ent._img.face;
			const {w, h} = Renderer.song.getRealSize_mm(ent);
			for (let i = 0; i < count; i++) {
				this._pdfFile.addPage([w + 2 * margin, h + 2 * margin], w > h ? "l" : "p");
				if (this._pdfCuttingGuide === "1" && margin) {
					this._pdfFile.addImage(src, 0, 0, w + 2 * margin, h + 2 * margin);
					const flipHorizontal = this._pdfFile.Matrix(-1, 0, 0, 1, 0, 0);
					const flipVertical = this._pdfFile.Matrix(1, 0, 0, -1, 0, 0);
					this._pdfFile.setCurrentTransformationMatrix(flipVertical);
					this._pdfFile.addImage(src, margin, 2 * h + 3 * margin, w, h);
					this._pdfFile.addImage(src, margin, 3 * margin, w, h);
					this._pdfFile.setCurrentTransformationMatrix(flipVertical);
					this._pdfFile.setCurrentTransformationMatrix(flipHorizontal);
					this._pdfFile.addImage(src, -2 * w - margin, margin, w, h);
					this._pdfFile.addImage(src, -margin, margin, w, h);
					this._pdfFile.setCurrentTransformationMatrix(flipHorizontal);
				}
				this._pdfFile.addImage(src, margin, margin, w, h);
			}
			// Wait a bit, otherwise the pdf library causes issues
			await MiscUtil.pDelay(5);
			completed += 1;
			const percentage = Math.ceil(100 * completed / items.length);
			this._updateProgressBar(percentage)
		}
	}

	// TODO: page might overflow if margin/padding too large
	async _preparePdf_FillPageA4 () {
		const margin = Number(this._pdfMargin);
		const padding = Number(this._pdfPadding);
		const items = this._sublistManager.sublistItems.sort((a, b) => SortUtil.ascSortLower(a.ix, b.ix));
		const units = items.filter(it => it.data.entity.__prop === "units").map(it => new Array(it.data.count).fill(it)).flat();
		const others = items.filter(it => it.data.entity.__prop !== "units").map(it => new Array(it.data.count).fill(it)).flat();

		let completed = 0;
		for (const other of others) {
			const ent = other.data.entity;
			const src = ent._img.face;
			const {w, h} = Renderer.song.getRealSize_mm(ent);
			let ixOnPage = completed % 8
			if (ixOnPage === 0) this._pdfFile.addPage("a4", "l");
			if (ixOnPage === 0 && this._pdfCuttingGuide === "1") {
				for (let i = 0; i < 4; i++) {
					const x_left = margin + i * (w + padding);
					const x_right = margin + i * padding + (i + 1) * w;
					const h_bottom = margin + 2 * h + padding + 0.5;
					this._pdfFile.line(x_left, 0, x_left, margin - 0.5, "S");
					if (padding > 0 || i === 3) this._pdfFile.line(x_right, 0, x_right, margin - 0.5, "S");
					this._pdfFile.line(x_left, h_bottom, x_left, 210, "S");
					if (padding > 0 || i === 3) this._pdfFile.line(x_right, h_bottom, x_right, 210, "S");
				}
				for (let i = 0; i < 2; i++) {
					const v_right = margin + 4 * w + 3 * padding + 0.5;
					const y_top = margin + i * (h + padding);
					const y_bottom = margin + i * padding + (i + 1) * h;
					this._pdfFile.line(0, y_top, margin - 0.5, y_top, "S");
					if (padding > 0 || i === 1) this._pdfFile.line(0, y_bottom, margin - 0.5, y_bottom, "S");
					this._pdfFile.line(v_right, y_top, 297, y_top, "S");
					if (padding > 0 || i === 1) this._pdfFile.line(v_right, y_bottom, 297, y_bottom, "S");
				}
			}
			this._pdfFile.addImage(src, margin + (ixOnPage % 4) * (w + padding), margin + Math.floor(ixOnPage / 4) * (h + padding), w, h);
			await MiscUtil.pDelay(5);
			completed += 1;
			const percentage = Math.ceil(100 * completed / items.length);
			this._updateProgressBar(percentage)
		}
		const offset = 8 - (completed % 8);

		for (const unit of units) {
			const ent = unit.data.entity;
			const src = ent._img.face;
			const {w, h} = Renderer.song.getRealSize_mm(ent);
			let ixOnPage = (completed + offset) % 4
			if (ixOnPage === 0) this._pdfFile.addPage("a4", "l");
			if (ixOnPage === 0 && this._pdfCuttingGuide === "1") {
				for (let i = 0; i < 2; i++) {
					const x_left = margin + i * (w + padding);
					const x_right = margin + i * padding + (i + 1) * w;
					const h_bottom = margin + 2 * h + padding + 0.5;
					this._pdfFile.line(x_left, 0, x_left, margin - 0.5, "S");
					this._pdfFile.line(x_right, 0, x_right, margin - 0.5, "S");
					this._pdfFile.line(x_left, h_bottom, x_left, 210, "S");
					this._pdfFile.line(x_right, h_bottom, x_right, 210, "S");

					const v_right = margin + 2 * w + padding + 0.5;
					const y_top = margin + i * (h + padding);
					const y_bottom = margin + i * padding + (i + 1) * h;
					this._pdfFile.line(0, y_top, margin - 0.5, y_top, "S");
					this._pdfFile.line(0, y_bottom, margin - 0.5, y_bottom, "S");
					this._pdfFile.line(v_right, y_top, 297, y_top, "S");
					this._pdfFile.line(v_right, y_bottom, 297, y_bottom, "S");
				}
			}
			this._pdfFile.addImage(src, margin + (ixOnPage % 2) * (w + padding), margin + Math.floor(ixOnPage / 2) * (h + padding), w, h);
			await MiscUtil.pDelay(5);
			completed += 1;
			const percentage = Math.ceil(100 * completed / items.length);
			this._updateProgressBar(percentage);
		}
	}

	async _preparePdf () {
		this._btnOpenPdf.hide();
		this._progressPdf.$wrapOuter.show();
		this._updateProgressBar(0);
		this._pdfFile = new jspdf.jsPDF();
		this._pdfFile.deletePage(1);
		if (this._printMode === "0") await this._preparePdf_FillPageA4();
		else if (this._printMode === "1") await this._preparePdf_Singletons();
		const blob = this._pdfFile.output("blob");
		const filename = `${this._sublistManager._saveManager._getActiveSave().entity.name || "asoiaf-tmg-data"}.pdf`;
		DataUtil.userDownloadBlob(filename, blob);
		this._progressPdf.$wrapOuter.hide();
		this._btnOpenPdf.show();
	}

	_updateProgressBar (numPercent) {
		const percent = `${numPercent}%`;
		this._progressPdf.$displayProgress.css("width", percent);
		this._$displayPercent.text(`Generating...  ${percent}`);
	};

	async _pGetRenderContentMeta ({$wrpContent, $wrpControls}) {
		this._$wrpContent = $wrpContent;
		$wrpContent.addClass("p-2");

		this._bookViewToShow = this._sublistManager.getSublistedEntities();

		const {isAnyEntityRendered} = this._renderEntities();

		return {
			cntSelectedEnts: this._bookViewToShow.length,
			isAnyEntityRendered,
		};
	}
}

class SongPage extends ListPageMultiSource {
	constructor () {
		super({
			pageFilter: new PageFilterSong(),

			dataProps: ["song", "units", "ncus", "attachments", "tactics"],

			bookViewOptions: {
				ClsBookView: SongPageBookView,
			},

			propLoader: "song",

			listSyntax: new ListSyntaxSong({fnGetDataList: () => this._dataList}),
		});

		this._lastFilterValues = null;
	}

	getListItem (obj, spI) {
		const hash = UrlUtil.autoEncodeHash(obj);
		if (this._seenHashes.has(hash)) return null;
		this._seenHashes.add(hash);

		this._pageFilter.mutateAndAddToFilters(obj);

		const source = obj.source;
		const faction = Parser.renderFaction(obj.statistics.faction);
		const type = Parser.renderProp(obj.__prop);

		const eleLi = e_({
			tag: "div",
			clazz: `lst__row ve-flex-col`,
			click: (evt) => this._list.doSelect(listItem, evt),
			contextmenu: (evt) => this._openContextMenu(evt, this._list, listItem),
			children: [
				e_({
					tag: "a",
					href: `#${hash}`,
					clazz: "lst--border lst__row-inner",
					children: [
						e_({tag: "span", clazz: `ve-col-6-5 pl-0`, children: [
							e_({tag: "span", clazz: "bold", text: obj._fullName}),
							obj.__prop === "tactics" ? e_({tag: "span", clazz: "ve-muted", text: ` (${obj.statistics.commander_name || faction})`}) : undefined,
						].filter(Boolean)}),
						e_({tag: "span", clazz: `ve-col-2-5 text-center`, text: faction}),
						e_({tag: "span", clazz: `ve-col-2 text-center`, text: type}),
						e_({tag: "span", clazz: `ve-col-1 ve-text-center pr-0`, text: source}),
					],
				}),
			],
		});

		const listItem = new ListItem(
			spI,
			eleLi,
			obj.name,
			{
				hash,
				source,
				faction,
				type,
			},
			{
			},
		);

		return listItem;
	}

	_tabTitleStats = "Face";
	_renderStats_doBuildStatsTab ({ent}, opts) {
		this._$pgContent.empty().append(Renderer.song.getRenderedString(ent, opts));
	}

	_renderStats_getTabMetasAdditional ({ent}) {
		if (ent._img.back == null) return [];

		return [
			new Renderer.utils.TabButton({
				label: "Back",
				fnPopulate: () => this._renderStats_doBuildStatsTab({ent}, {isBack: true}),
				isVisible: true,
			}),
		]
	}
	async _pPreloadSublistSources (json) {
		const loaded = Object.keys(this._loadedSources)
			.filter(it => this._loadedSources[it].loaded);
		const lowerSources = json.sources.map(it => it.toLowerCase());
		const toLoad = Object.keys(this._loadedSources)
			.filter(it => !loaded.includes(it))
			.filter(it => lowerSources.includes(it.toLowerCase()));
		const loadTotal = toLoad.length;
		if (loadTotal) {
			await Promise.all(toLoad.map(src => this._pLoadSource(src, "yes")));
		}
	}

	async pHandleUnknownHash (link, sub) {
		const src = Object.keys(this._loadedSources)
			.find(src => src.toLowerCase() === (UrlUtil.decodeHash(link)[1] || "").toLowerCase());
		if (src) {
			await this._pLoadSource(src, "yes");
			Hist.hashChange();
		}
	}
}

const songPage = new SongPage();
songPage.sublistManager = new SongSublistManager();
window.addEventListener("load", () => songPage.pOnLoad());
