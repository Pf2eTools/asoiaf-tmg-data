"use strict";

class _UtilListPage {
	static pDoMassPopout (evt, ele, entityHashTuples) {
		const elePos = ele.getBoundingClientRect();

		// do this in serial to have a "window cascade" effect
		for (let i = 0; i < entityHashTuples.length; ++i) {
			const {entity, hash} = entityHashTuples[i];
			const posOffset = Renderer.hover._BAR_HEIGHT * i;

			const page = UrlUtil.getCurrentPage();
			Renderer.hover.getShowWindow(
				Renderer.hover.$getHoverContent_stats(page, entity),
				Renderer.hover.getWindowPositionExact(
					elePos.x + posOffset,
					elePos.y + posOffset,
					evt,
				),
				{
					title: entity.name,
					isPermanent: true,
					pageUrl: `${page}#${hash}`,
					isBookContent: page === UrlUtil.PG_RECIPES,
					sourceData: entity,
					width: Renderer.hover._getDefaultWidth(entity)
				},
			);
		}
	}
}

class SublistCellTemplate {
	constructor (
		{
			name,
			css,
			colStyle,
		},
	) {
		this._name = name;
		this._css = css;
		this._colStyle = colStyle;
	}

	get name () { return this._name; }
	get colStyle () { return this._colStyle; }

	getCss (text) {
		return [
			this._css,
			text === VeCt.STR_NONE
				? "list-entry-none"
				: "",
		]
			.filter(Boolean)
			.join(" ");
	}
}

class SublistCell {
	constructor (
		{
			text,
			title,
			css,
			style,
		},
	) {
		this._text = text;
		this._title = title;
		this._css = css;
		this._style = style;
	}

	static renderHtml ({templates, cell, ix}) {
		const text = cell instanceof SublistCell ? cell._text : cell;
		const title = cell instanceof SublistCell ? cell._title : null;
		const cssCell = cell instanceof SublistCell ? cell._css : null;
		const style = cell instanceof SublistCell ? cell._style : null;

		const css = [
			templates[ix].getCss(text),
			cssCell,
		]
			.filter(Boolean)
			.join(" ");

		const attrs = [
			`class="${css}"`,
			title ? `title="${title.qq()}"` : "",
			style ? `style="${style}"` : "",
		]
			.filter(Boolean)
			.join(" ");

		return `<span ${attrs}>${text}</span>`;
	}
}

class SublistManager {
	static _SUB_HASH_PREFIX = "sublistselected";

	/**
	 * @param [opts]
	 * @param [opts.sublistListOptions] Other sublist options.
	 * @param [opts.isSublistItemsCountable] If the sublist items should be countable, i.e. have a quantity.
	 * @param [opts.shiftCountAddSubtract] If the sublist items should be countable, i.e. have a quantity.
	 */
	constructor (opts) {
		opts = opts || {};

		this._sublistListOptions = opts.sublistListOptions || {};
		this._isSublistItemsCountable = !!opts.isSublistItemsCountable;
		this._shiftCountAddSubtract = opts.shiftCountAddSubtract ?? 20;

		this._persistor = new SublistPersistor();

		this._saveManager = new SaveManager();
		this._plugins = [];

		this._listPage = null;

		this._listSub = null;

		this._hasLoadedState = false;
		this._isRolling = false;

		this._contextMenuListSub = null;

		this._$wrpContainer = null;
		this._$wrpSummaryControls = null;

		this._pSaveSublistDebounced = MiscUtil.debounce(this._pSaveSublist.bind(this), 50);
	}

	set listPage (val) { this._listPage = val; }

	get sublistItems () { return this._listSub?.items || []; }
	get isSublistItemsCountable () { return !!this._isSublistItemsCountable; }

	addPlugin (plugin) {
		this._plugins.push(plugin);
	}

	init () {
		this._listSub.init();

		this._plugins.forEach(plugin => plugin.initLate());
	}

	async pCreateSublist () {
		this._$wrpContainer = $("#sublistcontainer");

		this._listSub = new List({
			...this._sublistListOptions,
			$wrpList: $(`#sublist`),
			isUseJquery: true,
		});

		const $wrpBtnsSortSublist = $("#sublistsort");
		if ($wrpBtnsSortSublist.length) SortUtil.initBtnSortHandlers($wrpBtnsSortSublist, this._listSub);

		if (this._$wrpContainer.hasClass(`sublist--resizable`)) this._pBindSublistResizeHandlers();

		const {$wrp: $wrpSummaryControls, cbOnListUpdated} = this._saveManager.$getRenderedSummary({
			cbOnNew: (evt) => this.pHandleClick_new(evt),
			cbOnDuplicate: (evt) => this.pHandleClick_duplicate(evt),
			cbOnSave: (evt) => this.pHandleClick_save(evt),
			cbOnLoad: (evt) => this.pHandleClick_load(evt),
			cbOnReset: (evt, exportedSublist) => this.pDoLoadExportedSublist(exportedSublist),
			cbOnUpload: (evt) => this.pHandleClick_upload({isAdditive: evt.shiftKey}),
		});

		this._$wrpSummaryControls = $wrpSummaryControls;

		const hkOnListUpdated = () => cbOnListUpdated({cntVisibleItems: this._listSub.visibleItems.length});
		this._listSub.on("updated", hkOnListUpdated);
		hkOnListUpdated();

		this._$wrpContainer.after(this._$wrpSummaryControls);

		this._initContextMenu();

		this._listSub
			.on("updated", () => {
				this._plugins.forEach(plugin => plugin.onSublistUpdate());
			});
	}

	async _pBindSublistResizeHandlers () {
		const STORAGE_KEY = "SUBLIST_RESIZE";

		const $handle = $(`<div class="sublist__ele-resize mobile__hidden">...</div>`).appendTo(this._$wrpContainer);

		let mousePos;
		const resize = (evt) => {
			evt.preventDefault();
			evt.stopPropagation();
			const dx = EventUtil.getClientY(evt) - mousePos;
			mousePos = EventUtil.getClientY(evt);
			this._$wrpContainer.css("height", parseInt(this._$wrpContainer.css("height")) + dx);
		};

		$handle
			.on("mousedown", (evt) => {
				if (evt.which !== 1) return;

				evt.preventDefault();
				mousePos = evt.clientY;
				document.removeEventListener("mousemove", resize);
				document.addEventListener("mousemove", resize);
			});

		document.addEventListener("mouseup", evt => {
			if (evt.which !== 1) return;

			document.removeEventListener("mousemove", resize);
			StorageUtil.pSetForPage(STORAGE_KEY, this._$wrpContainer.css("height"));
		});

		// Avoid setting the height on mobile, as we force the sublist to a static size
		if (JqueryUtil.isMobile()) return;

		const storedHeight = await StorageUtil.pGetForPage(STORAGE_KEY);
		if (storedHeight) this._$wrpContainer.css("height", storedHeight);
	}

	_onSublistChange () { /* Implement as required */ }

	_getSerializedPinnedItemData (listItem) { return {}; }
	_getDeserializedPinnedItemData (serialData) { return null; }

	_getContextActionRemove () {
		return this._isSublistItemsCountable
			? new ContextUtil.Action(
				"Remove",
				async (evt, {userData}) => {
					const {selection} = userData;
					await Promise.all(selection.map(item => this.pDoSublistRemove({entity: item.data.entity, doFinalize: false})));
					await this._pFinaliseSublist();
				},
			)
			: new ContextUtil.Action(
				"Unpin",
				async (evt, {userData}) => {
					const {selection} = userData;
					for (const item of selection) {
						await this.pDoSublistRemove({entity: item.data.entity, doFinalize: false});
					}
					await this._pFinaliseSublist();
				},
			);
	}

	_initContextMenu () {
		const subActions = [
			new ContextUtil.Action(
				"Popout",
				(evt, {userData}) => {
					const {ele, selection} = userData;
					const entities = selection.map(listItem => ({entity: listItem.data.entity, hash: listItem.values.hash}));
					return _UtilListPage.pDoMassPopout(evt, ele, entities);
				},
			),
			this._getContextActionRemove(),
			new ContextUtil.Action(
				"Clear List",
				() => this.pDoSublistRemoveAll(),
			),
			null,
			new ContextUtil.Action(
				"Roll on List",
				(evt) => this._rollSubListed({evt}),
				{title: "SHIFT to Skip Animation"},
			),
			null,
			new ContextUtil.Action(
				"Download JSON Data",
				() => this._pHandleJsonDownload(),
			),
			null,
		].filter(it => it !== undefined);
		this._contextMenuListSub = ContextUtil.getMenu(subActions);
	}

	_handleSublistItemContextMenu (evt, listItem) {
		const menu = this._contextMenuListSub;

		const listSelected = this._listSub.getSelected();
		const isItemInSelection = listSelected.length && listSelected.some(li => li === listItem);
		const selection = isItemInSelection ? listSelected : [listItem];
		if (!isItemInSelection) {
			this._listSub.deselectAll();
			this._listSub.doSelect(listItem);
		}

		const ele = listItem.ele instanceof $ ? listItem.ele[0] : listItem.ele;
		ContextUtil.pOpenMenu(evt, menu, {userData: {ele: ele, selection}});
	}

	pGetSublistItem () { throw new Error(`Unimplemented!`); }

	async pDoSublistRemoveAll ({isNoSave = false} = {}) {
		this._listSub.removeAllItems();
		await this._plugins.pSerialAwaitMap(plugin => plugin.pHandleRemoveAll());
		await this._pFinaliseSublist({isNoSave});
	}

	/**
	 * @param isForceIncludePlugins
	 * @param isMemoryOnly If this export is for a temporary internal application, e.g. export-modify-import.
	 */
	async pGetExportableSublist ({isForceIncludePlugins = false, isMemoryOnly = false} = {}) {
		const sources = new Set();
		const toSave = this._listSub.items
			.map(it => {
				sources.add(it.data.entity.source);

				return {
					h: it.values.hash.split(HASH_PART_SEP)[0],
					c: it.data.count || undefined,
					customHashId: this._getCustomHashId({entity: it.data.entity}) || undefined,
					...this._getSerializedPinnedItemData(it),
				};
			});
		const exportedSublist = {items: toSave, sources: Array.from(sources)};

		this._saveManager.mutSaveableData({exportedSublist});
		await this._plugins.pSerialAwaitMap(plugin => plugin.pMutSaveableData({
			exportedSublist,
			isForce: isForceIncludePlugins,
			isMemoryOnly,
		}));

		return exportedSublist;
	}

	async pDoLoadExportedSublist (
		exportedSublist,
		{
			isAdditive = false,
			isMemoryOnly = false,
			isNoSave = false,
		} = {},
	) {
		// This should never be necessary, but, ensure no unwanted state gets passed
		if (exportedSublist) ListUtil.getWithoutManagerClientState(exportedSublist);

		// Note that `exportedSublist` keys are case-insensitive here, as we can load from URL
		await this._plugins.pSerialAwaitMap(plugin => plugin.pMutLegacyData({exportedSublist, isMemoryOnly}));

		if (exportedSublist && !isAdditive) await this.pDoSublistRemoveAll({isNoSave: true});

		await this._listPage.pDoLoadExportedSublistSources(exportedSublist);

		// Do this in series to ensure sublist items are added before having their counts updated
		//  This only becomes a problem when there are duplicate items in the list, but as we're not finalizing, the
		//  performance implications are negligible.
		const entityInfos = await ListUtil.pGetSublistEntities_fromList({
			exportedSublist,
			dataList: this._listPage.dataList_,
		});

		for (const entityInfo of entityInfos) {
			const {count, entity, ser} = entityInfo;

			await this.pDoSublistAdd({
				addCount: count,
				entity,
				initialData: this._getDeserializedPinnedItemData(ser),
				doFinalize: false,
			});
		}

		await this._plugins.pSerialAwaitMap(plugin => plugin.pLoadData({
			exportedSublist,
			isAdditive,
			isMemoryOnly,
		}));

		await this._saveManager.pDoUpdateCurrentStateFrom(exportedSublist, {isNoSave});

		await this._pFinaliseSublist({isNoSave});
	}

	async pGetHashPartExport () {
		const toEncode = JSON.stringify(await this.pGetExportableSublist());
		return UrlUtil.packSubHash(this.constructor._SUB_HASH_PREFIX, [toEncode], {isEncodeBoth: true});
	}

	async pHandleClick_btnPin ({entity}) {
		if (!this.isSublisted({entity})) {
			await this.pDoSublistAdd({entity, doFinalize: true});
			return;
		}

		await this.pDoSublistRemove({entity, doFinalize: true});
	}

	getTitleBtnAdd () { return `Add (SHIFT for ${this._shiftCountAddSubtract})`; }
	getTitleBtnSubtract () { return `Subtract (SHIFT for ${this._shiftCountAddSubtract})`; }

	async pHandleClick_btnAdd ({evt, entity}) {
		const addCount = evt.shiftKey ? this._shiftCountAddSubtract : 1;
		return this.pDoSublistAdd({
			index: Hist.lastLoadedId,
			entity,
			doFinalize: true,
			addCount,
		});
	}

	async pHandleClick_btnSubtract ({evt, entity}) {
		const subtractCount = evt.shiftKey ? this._shiftCountAddSubtract : 1;
		return this.pDoSublistSubtract({
			index: Hist.lastLoadedId,
			entity,
			subtractCount,
		});
	}

	async pHandleClick_btnAddAll ({entities}) {
		for (const entity of entities) await this.pDoSublistAdd({entity});
		await this._pFinaliseSublist();
	}

	async pHandleClick_btnPinAll ({entities}) {
		for (const entity of entities) {
			if (!this.isSublisted({entity})) await this.pDoSublistAdd({entity});
		}
		await this._pFinaliseSublist();
	}

	getPinnedEntities () {
		return this._listSub.items
			.map(({data}) => data.entity);
	}

	async _pHandleJsonDownload () {
		const entities = await this.getPinnedEntities();
		entities.forEach(ent => DataUtil.cleanJson(MiscUtil.copyFast(ent)));
		DataUtil.userDownload(`${this._getDownloadName()}-data`, entities);
	}

	async pHandleClick_new (evt) {
		const exportableSublist = await this.pGetExportableSublist({isForceIncludePlugins: true});
		const exportableSublistMemory = await this.pGetExportableSublist({isForceIncludePlugins: true, isMemoryOnly: true});
		const didNew = await this._saveManager.pDoNew(exportableSublist);
		if (!didNew) return;
		await this.pDoSublistRemoveAll();

		// Handle e.g. copying some aspects of the old state over
		await this._plugins.pSerialAwaitMap(plugin => plugin.pDoInitNewState({
			prevExportableSublist: exportableSublistMemory,
			evt,
		}));
	}

	async pHandleClick_duplicate (evt) {
		await this._saveManager.pDoDuplicate(await this.pGetExportableSublist({isForceIncludePlugins: true}));
	}

	async pHandleClick_load (evt) {
		const exportedSublist = await this._saveManager.pDoLoad();
		if (exportedSublist == null) return;

		await this.pDoLoadExportedSublist(exportedSublist);
	}

	async pHandleClick_save (evt) {
		const saveInfo = await this._saveManager.pDoSave(await this.pGetExportableSublist({isForceIncludePlugins: true}));
		if (saveInfo == null) return;

		await this._pSaveSublist();

		JqueryUtil.doToast(`Saved "${saveInfo.name}"!`);

		return true;
	}

	async pHandleClick_download ({isUrl = false, $eleCopyEffect = null} = {}) {
		const exportableSublist = await this.pGetExportableSublist();

		if (isUrl) {
			const parts = [
				window.location.href,
				await this.pGetHashPartExport(),
			];
			await MiscUtil.pCopyTextToClipboard(parts.join(HASH_PART_SEP));
			JqueryUtil.showCopiedEffect($eleCopyEffect);
			return;
		}

		const filename = this._getDownloadName();
		const fileType = this._getDownloadFileType();
		DataUtil.userDownload(filename, exportableSublist, {fileType});
	}

	async pHandleClick_upload ({isAdditive = false} = {}) {
		const {jsons, errors} = await DataUtil.pUserUpload({expectedFileTypes: this._getUploadFileTypes()});

		DataUtil.doHandleFileLoadErrorsGeneric(errors);

		if (!jsons?.length) return;

		const json = jsons[0];

		await this.pDoLoadExportedSublist(json, {isAdditive});
	}

	_getDownloadName () {
		const fromPlugin = this._plugins.first(plugin => plugin.getDownloadName());
		if (fromPlugin) return fromPlugin;
		return `${UrlUtil.getCurrentPage().replace(".html", "")}-sublist`;
	}

	_getDownloadFileTypeBase () {
		return `${UrlUtil.getCurrentPage().replace(".html", "")}-sublist`;
	}

	_getDownloadFileType () {
		const fromPlugin = this._plugins.first(plugin => plugin.getDownloadFileType());
		if (fromPlugin) return fromPlugin;
		return this._getDownloadFileTypeBase();
	}

	_getUploadFileTypes () {
		const fromPlugin = this._plugins.first(plugin => plugin.getUploadFileTypes({
			downloadFileTypeBase: this._getDownloadFileTypeBase(),
		}));
		if (fromPlugin) return fromPlugin;
		return [this._getDownloadFileType()];
	}

	async pSetFromSubHashes (subHashes, pFnPreLoad) {
		// TODO(unpack) refactor
		const unpacked = {};
		subHashes.forEach(s => {
			const unpackedPart = UrlUtil.unpackSubHash(s, true);
			if (Object.keys(unpackedPart).length > 1) throw new Error(`Multiple keys in subhash!`);
			const k = Object.keys(unpackedPart)[0];
			unpackedPart[k] = {clean: unpackedPart[k], raw: s};
			Object.assign(unpacked, unpackedPart);
		});

		const setFrom = unpacked[this.constructor._SUB_HASH_PREFIX]?.clean;
		if (setFrom) {
			const json = JSON.parse(setFrom);

			if (pFnPreLoad) {
				await pFnPreLoad(json);
			}

			await this.pDoLoadExportedSublist(json);

			const [link] = Hist.getHashParts();
			const outSub = [];
			Object.keys(unpacked)
				.filter(k => k !== this.constructor._SUB_HASH_PREFIX)
				.forEach(k => {
					outSub.push(`${k}${HASH_SUB_KV_SEP}${unpacked[k].clean.join(HASH_SUB_LIST_SEP)}`);
				});
			Hist.setSuppressHistory(true);
			window.location.hash = `#${link}${outSub.length ? `${HASH_PART_SEP}${outSub.join(HASH_PART_SEP)}` : ""}`;
		}

		return Object.entries(unpacked)
			.filter(([k]) => k !== this.constructor._SUB_HASH_PREFIX)
			.map(([, v]) => v.raw);
	}

	getSublistListItem ({hash}) {
		return this._listSub.items.find(it => it.values.hash === hash);
	}

	async pDoSublistAdd ({entity, doFinalize = false, addCount = 1, initialData = null} = {}) {
		if (entity == null) {
			return JqueryUtil.doToast({
				content: "Please first view something from the list.",
				type: "danger",
			});
		}

		const hash = this._getSublistFullHash({entity});

		const existingSublistItem = this.getSublistListItem({hash});
		if (existingSublistItem != null) {
			existingSublistItem.data.count += addCount;
			this._updateSublistItemDisplays(existingSublistItem);
			if (doFinalize) await this._pFinaliseSublist();
			return;
		}

		const sublistItem = await this.pGetSublistItem(
			entity,
			hash,
			{
				count: addCount,
				customHashId: this._getCustomHashId({entity}),
				initialData,
			},
		);
		this._listSub.addItem(sublistItem);
		if (doFinalize) await this._pFinaliseSublist();
	}

	_getSublistFullHash ({entity}) {
		return UrlUtil.autoEncodeHash(entity);
	}

	_getCustomHashId ({entity}) { return null; }

	async pDoSublistSubtract ({entity, subtractCount = 1} = {}) {
		const hash = this._getSublistFullHash({entity});

		const sublistItem = this.getSublistListItem({hash});
		if (!sublistItem) return;

		sublistItem.data.count -= subtractCount;
		if (sublistItem.data.count <= 0) {
			await this.pDoSublistRemove({entity, doFinalize: true});
			return;
		}

		this._updateSublistItemDisplays(sublistItem);
		await this._pFinaliseSublist();
	}

	async pSetDataEntry ({sublistItem, key, value}) {
		sublistItem.data[key] = value;
		this._updateSublistItemDisplays(sublistItem);
		await this._pFinaliseSublist();
	}

	getSublistedEntities () {
		return this._listSub.items.map(({data}) => data.entity);
	}

	_updateSublistItemDisplays (sublistItem) {
		(sublistItem.data.$elesCount || [])
			.forEach($ele => {
				if ($ele.is("input")) $ele.val(sublistItem.data.count);
				else $ele.text(sublistItem.data.count);
			});

		(sublistItem.data.fnsUpdate || [])
			.forEach(fn => fn());
	}

	async _pFinaliseSublist ({isNoSave = false} = {}) {
		const isUpdateFired = this._listSub.update();

		// Manually trigger plugin updates if the list failed to do so
		if (!isUpdateFired) this._plugins.forEach(plugin => plugin.onSublistUpdate());

		this._updateSublistVisibility();
		this._onSublistChange();
		if (!isNoSave) await this._pSaveSublist();
	}

	async _pSaveSublist () {
		await this._persistor.pDoSaveStateToStorage({
			exportableSublist: await this.pGetExportableSublist({isForceIncludePlugins: true}),
		});
		await this._saveManager.pDoSaveStateToStorage();
	}

	async pSaveSublistDebounced () {
		return this._pSaveSublistDebounced();
	}

	_updateSublistVisibility () {
		this._$wrpContainer.toggleClass("sublist--visible", !!this._listSub.items.length);
		this._$wrpSummaryControls.toggleVe(!!this._listSub.items.length);
	}

	async pDoSublistRemove ({entity, doFinalize = true} = {}) {
		const hash = this._getSublistFullHash({entity});
		const sublistItem = this.getSublistListItem({hash});
		if (!sublistItem) return;
		this._listSub.removeItem(sublistItem);
		if (doFinalize) await this._pFinaliseSublist();
	}

	isSublisted ({entity}) {
		const hash = this._getSublistFullHash({entity});
		return !!this.getSublistListItem({hash});
	}

	async pLoadState () {
		if (this._hasLoadedState) return;
		this._hasLoadedState = true;
		try {
			const store = await this._persistor.pGetStateFromStorage();
			await this.pDoLoadExportedSublist(store, {isNoSave: true});

			await this._saveManager.pMutStateFromStorage();
		} catch (e) {
			setTimeout(() => { throw e; });
			await this._saveManager.pDoRemoveStateFromStorage();
			await this._persistor.pDoRemoveStateFromStorage();
		}
	}

	async pGetSelectedSources () {
		let store;
		try {
			store = await this._persistor.pGetStateFromStorage();
		} catch (e) {
			setTimeout(() => { throw e; });
		}
		if (store?.sources) return store.sources;
		return [];
	}

	static async pDeserializeExportedSublistItem (serialItem) {
		const page = UrlUtil.getCurrentPage();
		const entityBase = await DataLoader.pCacheAndGetHash(page, serialItem.h);
		return {
			entity: entityBase,
			entityBase: serialItem.customHashId != null ? entityBase : null,
			count: serialItem.c,
			isLocked: !!serialItem.l,
			customHashId: serialItem.customHashId,
		};
	}

	_rollSubListed ({evt}) {
		if (this._isRolling) return;

		if (this._listSub.items.length <= 1) {
			return JqueryUtil.doToast({
				content: "Not enough entries to roll!",
				type: "danger",
			});
		}

		// Skip animation if SHIFT is pressed
		if (evt.shiftKey) {
			evt.preventDefault();
			const listItem = RollerUtil.rollOnArray(this._listSub.items);
			$(listItem.ele).click();
			return;
		}

		const timerMult = RollerUtil.randomise(125, 75);
		const timers = [0, 1, 1, 1, 1, 1, 1.5, 1.5, 1.5, 2, 2, 2, 2.5, 3, 4, -1] // last element is always sliced off
			.map(it => it * timerMult)
			.slice(0, -RollerUtil.randomise(4));

		function generateSequence (array, length) {
			const out = [RollerUtil.rollOnArray(array)];
			for (let i = 0; i < length; ++i) {
				let next = RollerUtil.rollOnArray(array);
				while (next === out.last()) {
					next = RollerUtil.rollOnArray(array);
				}
				out.push(next);
			}
			return out;
		}

		if (this._isRolling) return;

		this._isRolling = true;
		const $eles = this._listSub.items
			.map(it => $(it.ele).find(`a`));

		const $sequence = generateSequence($eles, timers.length);

		let total = 0;
		timers.map((it, i) => {
			total += it;
			setTimeout(() => {
				$sequence[i][0].click();
				if (i === timers.length - 1) this._isRolling = false;
			}, total);
		});
	}

	doSublistDeselectAll () { this._listSub.deselectAll(); }

	/* -------------------------------------------- */

	static get _ROW_TEMPLATE () { throw new Error("Unimplemented"); }

	static _doValidateRowTemplateValues ({values, templates}) {
		if (values.length !== templates.length) throw new Error(`Length of row template and row values did not match! This is a bug!`);
	}

	/**
	 * @param values
	 * @param {Array<SublistCellTemplate>} templates
	 */
	static _getRowCellsHtml ({values, templates = null}) {
		templates = templates || this._ROW_TEMPLATE;
		this._doValidateRowTemplateValues({values, templates});
		return values
			.map((val, i) => SublistCell.renderHtml({templates, cell: val, ix: i}))
			.join("");
	}

	static _getRowEntryColLabels () { return this._ROW_TEMPLATE.map(it => it.name); }
	static _getRowEntryColStyles () { return this._ROW_TEMPLATE.map(it => it.colStyle); }
}

class ListPageStateManager extends BaseComponent {
	static _STORAGE_KEY;

	async pInit () {
		const saved = await this._pGetPersistedState();
		if (!saved) return;
		this.setStateFrom(saved);
	}

	async _pGetPersistedState () {
		return StorageUtil.pGetForPage(this.constructor._STORAGE_KEY);
	}

	async _pPersistState () {
		await StorageUtil.pSetForPage(this.constructor._STORAGE_KEY, this.getSaveableState());
	}

	addHookBase (prop, hk) { return this._addHookBase(prop, hk); }
	removeHookBase (prop, hk) { return this._removeHookBase(prop, hk); }
}

class ListPageSettingsManager extends ListPageStateManager {
	static _STORAGE_KEY = "listPageSettings";

	static _SETTINGS = [];

	_getSettings () { return {}; }

	bindBtnOpen ({btn}) {
		if (!btn) return;

		btn
			.addEventListener(
				"click",
				() => {
					const $btnReset = $(`<button class="btn btn-default btn-xs" title="Reset"><span class="glyphicon glyphicon-refresh"></span></button>`)
						.click(() => {
							this._proxyAssignSimple("state", this._getDefaultState(), true);
							this._pPersistState()
								.then(() => Hist.hashChange());
						});

					const {$modalInner} = UiUtil.getShowModal({
						isIndestructible: true,
						isHeaderBorder: true,
						title: "Settings",
						cbClose: () => {
							this._pPersistState()
								.then(() => Hist.hashChange());
						},
						$titleSplit: $btnReset,
					});

					const $rows = Object.entries(this._getSettings())
						.map(([prop, setting]) => {
							switch (setting.type) {
								case "boolean": {
									return $$`<label class="split-v-center stripe-even py-1">
										<span>${setting.name}</span>
										${ComponentUiUtil.$getCbBool(this, prop)}
									</label>`;
								}

								case "enum": {
									return $$`<label class="split-v-center stripe-even py-1">
										<span>${setting.name}</span>
										${ComponentUiUtil.$getSelEnum(this, prop, {values: setting.enumVals})}
									</label>`;
								}

								default: throw new Error(`Unhandled type "${setting.type}"`);
							}
						});

					$$($modalInner)`<div class="ve-flex-col">
						${$rows}
					</div>`;
				},
			);
	}

	getValues () {
		return MiscUtil.copyFast(this.__state);
	}

	async pSet (key, val) {
		this._state[key] = val;
		await this._pPersistState();
	}

	get (key) { return this._state[key]; }

	_getDefaultState () {
		return SettingsUtil.getDefaultSettings(this._getSettings());
	}
}

class ListPage {
	/**
	 * @param opts Options object.
	 * @param opts.dataSource Main JSON data url or function to fetch main data.
	 * @param [opts.prereleaseDataSource] Function to fetch prerelease data.
	 * @param [opts.brewDataSource] Function to fetch brew data.
	 * @param [opts.pFnGetFluff] Function to fetch fluff for a given entity.
	 * @param [opts.dataSourceFluff] Fluff JSON data url or function to fetch fluff data.
	 * @param [opts.filters] Array of filters to use in the filter box. (Either `filters` and `filterSource` or
	 * `pageFilter` must be specified.)
	 * @param [opts.filterSource] Source filter. (Either `filters` and `filterSource` or
	 * `pageFilter` must be specified.)
	 * @param [opts.pageFilter] PageFilter implementation for this page. (Either `filters` and `filterSource` or
	 * `pageFilter` must be specified.)
	 * @param opts.listOptions Other list options.
	 * @param opts.dataProps JSON data propert(y/ies).
	 *
	 * @param [opts.bookViewOptions] Book view options.
	 * @param [opts.bookViewOptions.ClsBookView]
	 * @param [opts.bookViewOptions.pageTitle]
	 * @param [opts.bookViewOptions.namePlural]
	 * @param [opts.bookViewOptions.fnPartition]
	 *
	 * @param [opts.tableViewOptions] Table view options.
	 * @param [opts.isPreviewable] True if the entities can be previewed in-line as part of the list.
	 * @param [opts.isLoadDataAfterFilterInit] If the order of data loading and filter-state loading should be flipped.
	 * @param [opts.isBindHashHandlerUnknown] If the "unknown hash" handler function should be bound.
	 * @param [opts.propEntryData]
	 * @param [opts.listSyntax]
	 * @param [opts.compSettings]
	 */
	constructor (opts) {
		this._dataSource = opts.dataSource;
		this._prereleaseDataSource = opts.prereleaseDataSource;
		this._brewDataSource = opts.brewDataSource;
		this._pFnGetFluff = opts.pFnGetFluff;
		this._dataSourcefluff = opts.dataSourceFluff;
		this._filters = opts.filters;
		this._filterSource = opts.filterSource;
		this._pageFilter = opts.pageFilter;
		this._listOptions = opts.listOptions || {};
		this._dataProps = opts.dataProps;
		this._bookViewOptions = opts.bookViewOptions;
		this._tableViewOptions = opts.tableViewOptions;
		this._isPreviewable = opts.isPreviewable;
		this._isLoadDataAfterFilterInit = !!opts.isLoadDataAfterFilterInit;
		this._isBindHashHandlerUnknown = !!opts.isBindHashHandlerUnknown;
		this._propEntryData = opts.propEntryData;
		this._listSyntax = opts.listSyntax || new ListUiUtil.ListSyntax({fnGetDataList: () => this._dataList, pFnGetFluff: opts.pFnGetFluff});
		this._compSettings = opts.compSettings ? opts.compSettings : null;

		this._lockHashchange = new VeLock({name: "hashchange"});
		this._renderer = Renderer.get();
		this._list = null;
		this._filterBox = null;
		this._dataList = [];
		this._ixData = 0;
		this._bookView = null;
		this._bookViewToShow = null;
		this._sublistManager = null;
		this._btnsTabs = {};
		this._lastRender = {};

		this._$pgContent = null;
		this._$wrpTabs = null;

		this._contextMenuList = null;

		this._seenHashes = new Set();
	}

	get primaryLists () { return [this._list]; }
	get dataList_ () { return this._dataList; }

	set sublistManager (val) {
		this._sublistManager = val;
		val.listPage = this;
	}

	async pOnLoad () {
		Hist.setListPage(this);

		this._pOnLoad_findPageElements();

		await Promise.all([
			PrereleaseUtil.pInit(),
			BrewUtil2.pInit(),
		]);

		await this._pOnLoad_pInitSettingsManager();

		let data;
		// For pages which can load data without filter state, load the data early
		if (!this._isLoadDataAfterFilterInit) {
			await this._pOnLoad_pPreDataLoad();
			data = await this._pOnLoad_pGetData();
		}

		await this._pOnLoad_pInitPrimaryLists();

		// For pages which cannot load data without filter state, load the data late
		if (this._isLoadDataAfterFilterInit) {
			await this._pOnLoad_pPreDataLoad();
			data = await this._pOnLoad_pGetData();
		}

		this._pOnLoad_initVisibleItemsDisplay();

		if (this._filterBox) this._filterBox.on(FilterBox.EVNT_VALCHANGE, this.handleFilterChange.bind(this));

		if (this._sublistManager) {
			if (this._sublistManager.isSublistItemsCountable) {
				this._bindAddButton();
				this._bindSubtractButton();
			} else {
				this._bindPinButton();
			}
			this._initContextMenu();

			await this._sublistManager.pCreateSublist();
		}

		await this._pOnLoad_pPreDataAdd();

		this._addData(data);

		if (this._pageFilter) this._pageFilter.trimState();

		await this._pOnLoad_pLoadListState();

		this._pOnLoad_bindMiscButtons();

		this._pOnLoad_bookView();
		this._pOnLoad_tableView();

		// bind hash-change functions for hist.js to use
		window.loadHash = this.pDoLoadHash.bind(this);
		window.loadSubHash = this.pDoLoadSubHash.bind(this);
		if (this._isBindHashHandlerUnknown) window.pHandleUnknownHash = this.pHandleUnknownHash.bind(this);

		this.primaryLists.forEach(list => list.init());
		if (this._sublistManager) this._sublistManager.init();

		Hist.init(true);

		this.handleFilterChange();

		await this._pOnLoad_pPostLoad();

		window.dispatchEvent(new Event("toolsLoaded"));
	}

	_pOnLoad_findPageElements () {
		this._$pgContent = $(`#pagecontent`);
		this._$wrpTabs = $(`#stat-tabs`);
	}

	async _pOnLoad_pInitSettingsManager () {
		if (!this._compSettings) return;

		await this._compSettings.pInit();
		this._compSettings.bindBtnOpen({btn: document.getElementById("btn-list-settings")});
	}

	async _pOnLoad_pInitPrimaryLists () {
		const $iptSearch = $("#lst__search");
		const $btnReset = $("#reset");
		this._list = this._initList({
			$iptSearch,
			$wrpList: $(`#list`),
			$btnReset,
			$btnClear: $(`#lst__search-glass`),
			dispPageTagline: document.getElementById(`page__subtitle`),
			isPreviewable: this._isPreviewable,
			syntax: this._listSyntax.build(),
			isBindFindHotkey: true,
			optsList: this._listOptions,
		});
		const $wrpBtnsSort = $("#filtertools");
		SortUtil.initBtnSortHandlers($wrpBtnsSort, this._list);
		if (this._isPreviewable) this._doBindPreviewAllButton($wrpBtnsSort.find(`[name="list-toggle-all-previews"]`));

		this._filterBox = await this._pageFilter.pInitFilterBox({
			$iptSearch,
			$wrpFormTop: $(`#filter-search-group`),
			$btnReset,
		});
	}

	_pOnLoad_initVisibleItemsDisplay () {
		const $outVisibleResults = $(`.lst__wrp-search-visible`);
		this._list.on("updated", () => $outVisibleResults.html(`${this._list.visibleItems.length}/${this._list.items.length}`));
	}

	async _pOnLoad_pLoadListState () {
		await this._sublistManager.pLoadState();
	}

	_pOnLoad_bindMiscButtons () {
		const $btnReset = $("#reset");
		ManageBrewUi.bindBtnOpen($(`#manage-brew`));
		this._renderListFeelingLucky({$btnReset});
		this._renderListShowHide({
			$wrpList: $(`#listcontainer`),
			$wrpContent: $(`#contentwrapper`),
			$btnReset,
		});
	}

	async _pOnLoad_pPreDataLoad () { /* Implement as required */ }
	async _pOnLoad_pPostLoad () { /* Implement as required */ }

	async pDoLoadExportedSublistSources (exportedSublist) { /* Implement as required */ }

	async _pOnLoad_pGetData () {
		const data = await (typeof this._dataSource === "string" ? DataUtil.loadJSON(this._dataSource) : this._dataSource());
		const prerelease = await (this._prereleaseDataSource ? this._prereleaseDataSource() : PrereleaseUtil.pGetBrewProcessed());
		const homebrew = await (this._brewDataSource ? this._brewDataSource() : BrewUtil2.pGetBrewProcessed());

		return BrewUtil2.getMergedData(PrereleaseUtil.getMergedData(data, prerelease), homebrew);
	}

	_pOnLoad_bookView () {
		if (!this._bookViewOptions) return;

		this._bookView = new (this._bookViewOptions.ClsBookView || ListPageBookView)({
			...this._bookViewOptions,
			sublistManager: this._sublistManager,
			fnGetEntLastLoaded: () => this._dataList[Hist.lastLoadedId],
			$btnOpen: $(`#btn-book`),
		});
	}

	_pOnLoad_tableView () {
		if (!this._tableViewOptions) return;

		$(`#btn-show-table`)
			.click(() => {
				const sublisted = this._sublistManager.getSublistedEntities();
				UtilsTableview.show({
					entities: sublisted.length
						? sublisted
						: this.primaryLists
							.map(list => list.visibleItems.map(({ix}) => this._dataList[ix]))
							.flat(),
					sorter: (a, b) => SortUtil.ascSort(a.name, b.name) || SortUtil.ascSort(a.source, b.source),
					...this._tableViewOptions,
				});
			});
	}

	async _pOnLoad_pPreDataAdd () { /* Implement as required */ }

	_addData (data) {
		if (!this._dataProps.some(prop => data[prop] && data[prop].length)) return;

		this._dataProps.forEach(prop => {
			if (!data[prop]) return;
			this._dataList.push(...data[prop]);
		});

		const len = this._dataList.length;
		for (; this._ixData < len; this._ixData++) {
			const it = this._dataList[this._ixData];
			const listItem = this.getListItem(it, this._ixData);
			if (!listItem) continue;
			if (this._isPreviewable) this._doBindPreview(listItem);
			this._addListItem(listItem);
		}

		this.primaryLists.forEach(list => list.update());
		this._filterBox.render();
		if (!Hist.initialLoad) this.handleFilterChange();

		this._bindPopoutButton();
		this._bindLinkExportButton(this._filterBox);
		this._bindOtherButtons({
			...(this._bindOtherButtonsOptions || {}),
		});
	}

	/* Implement as required */
	get _bindOtherButtonsOptions () { return null; }

	_addListItem (listItem) {
		this._list.addItem(listItem);
	}

	_doBindPreviewAllButton ($btn) {
		$btn
			.click(() => {
				const isExpand = $btn.html() === `[+]`;
				$btn.html(isExpand ? `[\u2012]` : "[+]");

				this.primaryLists.forEach(list => {
					list.visibleItems.forEach(listItem => {
						const {btnToggleExpand, dispExpandedOuter, dispExpandedInner} = this._getPreviewEles(listItem);
						if (isExpand) this._doPreviewExpand({listItem, dispExpandedOuter, btnToggleExpand, dispExpandedInner});
						else this._doPreviewCollapse({dispExpandedOuter, btnToggleExpand, dispExpandedInner});
					});
				});
			});
	}

	/** Requires a "[+]" button as the first list column, and the item to contain a second hidden display element. */
	_doBindPreview (listItem) {
		const {btnToggleExpand, dispExpandedOuter, dispExpandedInner} = this._getPreviewEles(listItem);

		dispExpandedOuter.addEventListener("click", evt => {
			evt.stopPropagation();
		});

		btnToggleExpand.addEventListener("click", evt => {
			evt.stopPropagation();
			evt.preventDefault();

			this._doPreviewToggle({listItem, btnToggleExpand, dispExpandedInner, dispExpandedOuter});
		});
	}

	_getPreviewEles (listItem) {
		const btnToggleExpand = listItem.ele.firstElementChild.firstElementChild;
		const dispExpandedOuter = listItem.ele.lastElementChild;
		const dispExpandedInner = dispExpandedOuter.lastElementChild;

		return {
			btnToggleExpand,
			dispExpandedOuter,
			dispExpandedInner,
		};
	}

	_doPreviewToggle ({listItem, btnToggleExpand, dispExpandedInner, dispExpandedOuter}) {
		const isExpand = btnToggleExpand.innerHTML === `[+]`;
		if (isExpand) this._doPreviewExpand({listItem, dispExpandedOuter, btnToggleExpand, dispExpandedInner});
		else this._doPreviewCollapse({dispExpandedOuter, btnToggleExpand, dispExpandedInner});
	}

	_doPreviewExpand ({listItem, dispExpandedOuter, btnToggleExpand, dispExpandedInner}) {
		dispExpandedOuter.classList.remove("ve-hidden");
		btnToggleExpand.innerHTML = `[\u2012]`;
		Renderer.hover.$getHoverContent_stats(UrlUtil.getCurrentPage(), this._dataList[listItem.ix]).appendTo(dispExpandedInner);
	}

	_doPreviewCollapse ({dispExpandedOuter, btnToggleExpand, dispExpandedInner}) {
		dispExpandedOuter.classList.add("ve-hidden");
		btnToggleExpand.innerHTML = `[+]`;
		dispExpandedInner.innerHTML = "";
	}

	// ==================

	_renderListShowHide ({$wrpContent, $wrpList, $btnReset}) {
		const $btnHideSearch = $(`<button class="btn btn-default" title="Hide Search Bar and Entry List">Hide</button>`);
		$btnReset.before($btnHideSearch);

		const $btnShowSearch = $(`<button class="btn btn-block btn-default btn-xs" type="button">Show List</button>`);
		const $wrpBtnShowSearch = $$`<div class="ve-col-12 mb-1 ve-hidden">${$btnShowSearch}</div>`.prependTo($wrpContent);

		$btnHideSearch.click(() => {
			$wrpList.hideVe();
			$wrpBtnShowSearch.showVe();
			$btnHideSearch.hideVe();
		});
		$btnShowSearch.click(() => {
			$wrpList.showVe();
			$wrpBtnShowSearch.hideVe();
			$btnHideSearch.showVe();
		});
	}

	_renderListFeelingLucky ({isCompact, $btnReset}) {
		const $btnRoll = $(`<button class="btn btn-default ${isCompact ? "px-2" : ""}" title="Feeling Lucky?"><span class="glyphicon glyphicon-random"></span></button>`);

		$btnRoll.on("click", () => {
			const allLists = this.primaryLists.filter(l => l.visibleItems.length);
			if (allLists.length) {
				const rollX = RollerUtil.roll(allLists.length);
				const list = allLists[rollX];
				const rollY = RollerUtil.roll(list.visibleItems.length);
				window.location.hash = $(list.visibleItems[rollY].ele).find(`a`).prop("hash");
				list.visibleItems[rollY].ele.scrollIntoView();
			}
		});

		$btnReset.before($btnRoll);
	}

	_bindLinkExportButton ({$btn} = {}) {
		$btn = $btn || this._getOrTabRightButton(`link-export`, `magnet`);
		$btn.addClass("btn-copy-effect")
			.off("click")
			.on("click", async evt => {
				let url = window.location.href;

				if (EventUtil.isCtrlMetaKey(evt)) {
					await MiscUtil.pCopyTextToClipboard(this._filterBox.getFilterTag({isAddSearchTerm: true}));
					JqueryUtil.showCopiedEffect($btn);
					return;
				}

				const parts = this._filterBox.getSubHashes({isAddSearchTerm: true});
				parts.unshift(url);

				if (evt.shiftKey && this._sublistManager) {
					parts.push(await this._sublistManager.pGetHashPartExport());
				}

				await MiscUtil.pCopyTextToClipboard(parts.join(HASH_PART_SEP));
				JqueryUtil.showCopiedEffect($btn);
			})
			.title("Get link to filters (SHIFT adds list; CTRL copies @filter tag)");
	}

	_bindPopoutButton () {
		this._getOrTabRightButton(`popout`, `new-window`)
			.off("click")
			.title(`Popout Window (SHIFT for Source Data)`)
			.on(
				"click",
				(evt) => {
					if (Hist.lastLoadedId === null) return;

					return this._bindPopoutButton_doShowStatblock(evt);
				},
			);
	}

	_bindPopoutButton_doShowStatblock (evt) {
		if (!evt.shiftKey) return Renderer.hover.doPopoutCurPage(evt, this._lastRender.entity);

		const $content = Renderer.hover.$getHoverContent_statsCode(this._lastRender.entity);
		Renderer.hover.getShowWindow(
			$content,
			Renderer.hover.getWindowPositionFromEvent(evt),
			{
				title: `${this._lastRender.entity.name} \u2014 Source Data`,
				isPermanent: true,
				isBookContent: true,
				width: 750
			},
		);
	}

	_initList (
		{
			$iptSearch,
			$wrpList,
			$btnReset,
			$btnClear,
			dispPageTagline,
			isPreviewable,
			isBindFindHotkey,
			syntax,
			optsList,
		},
	) {
		const helpText = [];
		if (isBindFindHotkey) helpText.push(`Hotkey: f.`);

		const list = new List({$iptSearch, $wrpList, syntax, helpText, ...optsList});

		if (isBindFindHotkey) {
			$(document.body).on("keypress", (evt) => {
				if (!EventUtil.noModifierKeys(evt) || EventUtil.isInInput(evt)) return;
				if (EventUtil.getKeyIgnoreCapsLock(evt) === "f") {
					evt.preventDefault();
					$iptSearch.select().focus();
				}
			});
		}

		$btnReset.click(() => {
			$iptSearch.val("");
			list.reset();
		});

		// region Magnifying glass/clear button
		$btnClear
			.click(() => $iptSearch.val("").change().keydown().keyup().focus());
		const _handleSearchChange = () => {
			setTimeout(() => {
				const hasText = !!$iptSearch.val().length;

				$btnClear
					.toggleClass("no-events", !hasText)
					.toggleClass("clickable", hasText)
					.title(hasText ? "Clear" : null)
					.html(`<span class="glyphicon ${hasText ? `glyphicon-remove` : `glyphicon-search`}"></span>`);
			});
		};
		const handleSearchChange = MiscUtil.throttle(_handleSearchChange, 50);
		$iptSearch.on("keydown", handleSearchChange);
		// endregion

		if (dispPageTagline) {
			dispPageTagline.innerHTML += ` Press J/K to navigate${isPreviewable ? `, M to expand` : ""}.`;
			this._initList_bindWindowHandlers();
		}

		return list;
	}

	_initList_scrollToItem () {
		const toShow = Hist.getSelectedListElementWithLocation();

		if (toShow) {
			const $li = $(toShow.item.ele);
			const $wrpList = $li.parent();
			const parentScroll = $wrpList.scrollTop();
			const parentHeight = $wrpList.height();
			const posInParent = $li.position().top;
			const height = $li.height();

			if (posInParent < 0) {
				$li[0].scrollIntoView();
			} else if (posInParent + height > parentHeight) {
				$wrpList.scrollTop(parentScroll + (posInParent - parentHeight + height));
			}
		}
	}

	_initList_bindWindowHandlers () {
		window.addEventListener("keypress", (evt) => {
			if (!EventUtil.noModifierKeys(evt)) return;

			const key = EventUtil.getKeyIgnoreCapsLock(evt);
			switch (key) {
				// K up; J down
				case "k":
				case "j": {
					// don't switch if the user is typing somewhere else
					if (EventUtil.isInInput(evt)) return;
					this._initList_handleListUpDownPress(key === "k" ? -1 : 1);
					return;
				}

				case "m": {
					if (EventUtil.isInInput(evt)) return;
					const it = Hist.getSelectedListElementWithLocation();
					$(it.item.ele.firstElementChild.firstElementChild).click();
				}
			}
		});
	}

	_initList_handleListUpDownPress (dir) {
		const it = Hist.getSelectedListElementWithLocation();
		if (!it) return;

		const lists = this.primaryLists;

		const ixVisible = it.list.visibleItems.indexOf(it.item);
		if (!~ixVisible) {
			// If the currently-selected item is not visible, jump to the top/bottom of the list
			const listsWithVisibleItems = lists.filter(list => list.visibleItems.length);
			const tgtItem = dir === 1
				? listsWithVisibleItems[0].visibleItems[0]
				: listsWithVisibleItems.last().visibleItems.last();
			if (tgtItem) {
				window.location.hash = tgtItem.values.hash;
				this._initList_scrollToItem();
			}
			return;
		}

		const tgtItemSameList = it.list.visibleItems[ixVisible + dir];
		if (tgtItemSameList) {
			window.location.hash = tgtItemSameList.values.hash;
			this._initList_scrollToItem();
			return;
		}

		let ixListOther = it.x + dir;

		if (ixListOther === -1) ixListOther = lists.length - 1;
		else if (ixListOther === lists.length) ixListOther = 0;

		for (; ixListOther >= 0 && ixListOther < lists.length; ixListOther += dir) {
			if (!lists[ixListOther]?.visibleItems?.length) continue;

			const tgtItemOtherList = dir === 1 ? lists[ixListOther].visibleItems[0] : lists[ixListOther].visibleItems.last();
			if (!tgtItemOtherList) continue;

			window.location.hash = tgtItemOtherList.values.hash;
			this._initList_scrollToItem();
			return;
		}
	}

	_updateSelected () {
		const curSelectedItem = Hist.getSelectedListItem();
		this.primaryLists.forEach(l => l.updateSelected(curSelectedItem));
	}

	_openContextMenu (evt, list, listItem) {
		const listsWithSelections = this.primaryLists.map(l => ({l, selected: l.getSelected()}));

		let selection;
		if (listsWithSelections.some(it => it.selected.length)) {
			const isItemInSelection = listsWithSelections.some(it => it.selected.some(li => li === listItem));
			if (isItemInSelection) {
				selection = listsWithSelections.map(it => it.selected).flat();
				// trigger a context menu event with all the selected items
			} else {
				this.primaryLists.forEach(l => l.deselectAll());
				list.doSelect(listItem);
				selection = [listItem];
			}
		} else {
			list.doSelect(listItem);
			selection = [listItem];
		}

		ContextUtil.pOpenMenu(evt, this._contextMenuList, {userData: {ele: listItem.ele, selection}});
	}

	_initContextMenu () {
		if (this._contextMenuList) return;

		this._contextMenuList = ContextUtil.getMenu([
			new ContextUtil.Action(
				"Popout",
				async (evt, {userData}) => {
					const {ele, selection} = userData;
					await this._handleGenericContextMenuClick_pDoMassPopout(evt, ele, selection);
				},
			),
			this._getContextActionAdd(),
		]);
	}

	_getContextActionAdd () {
		const getEntities = () => this.primaryLists
			.map(list => list.getSelected()
				.map(li => {
					li.isSelected = false;
					return this._dataList[li.ix];
				}),
			)
			.flat();

		return this._sublistManager.isSublistItemsCountable
			? new ContextUtil.Action(
				"Add",
				async () => {
					await this._sublistManager.pHandleClick_btnAddAll({entities: getEntities()});
					this._updateSelected();
				},
			)
			: new ContextUtil.Action(
				"Pin",
				async () => {
					await this._sublistManager.pHandleClick_btnPinAll({entities: getEntities()});
					this._updateSelected();
				},
			);
	}

	_getOrTabRightButton (ident, icon, {title} = {}) {
		if (this._btnsTabs[ident]) return $(this._btnsTabs[ident]);

		this._btnsTabs[ident] = e_({
			tag: "button",
			clazz: "ui-tab__btn-tab-head btn btn-default",
			children: [
				e_({
					tag: "span",
					clazz: `glyphicon glyphicon-${icon}`,
				}),
			],
			title,
		});

		const wrpBtns = document.getElementById("tabs-right");
		wrpBtns.appendChild(this._btnsTabs[ident]);

		return $(this._btnsTabs[ident]);
	}

	_bindPinButton () {
		this._getOrTabRightButton(`pin`, `pushpin`)
			.off("click")
			.on("click", () => this._sublistManager.pHandleClick_btnPin({entity: this._lastRender.entity}))
			.title("Pin (Toggle)");
	}

	_bindAddButton () {
		this._getOrTabRightButton(`sublist-add`, `plus`)
			.off("click")
			.title(this._sublistManager.getTitleBtnAdd())
			.on("click", evt => this._sublistManager.pHandleClick_btnAdd({evt, entity: this._lastRender.entity}));
	}

	_bindSubtractButton () {
		this._getOrTabRightButton(`sublist-subtract`, `minus`)
			.off("click")
			.title(this._sublistManager.getTitleBtnSubtract())
			.on("click", evt => this._sublistManager.pHandleClick_btnSubtract({evt, entity: this._lastRender.entity}));
	}

	/**
	 * @param opts
	 * @param [opts.download]
	 * @param [opts.upload]
	 * @param [opts.upload.pPreloadSublistSources]
	 * @param [opts.sendToBrew]
	 * @param [opts.sendToBrew.fnGetMeta]
	 */
	_bindOtherButtons (opts) {
		opts = opts || {};

		const $btnOptions = this._getOrTabRightButton(`sublist-other`, `option-vertical`, {title: "Other Options"});

		const contextOptions = [
			new ContextUtil.Action(
				"New Pinned List",
				evt => this._sublistManager.pHandleClick_new(evt),
			),
			new ContextUtil.Action(
				"Load Pinned List",
				evt => this._sublistManager.pHandleClick_load(evt),
			),
			new ContextUtil.Action(
				"Save Pinned List",
				evt => this._sublistManager.pHandleClick_save(evt),
			),
			null,
			new ContextUtil.Action(
				"Download Pinned List (SHIFT to Copy Link)",
				evt => this._sublistManager.pHandleClick_download({isUrl: evt.shiftKey, $eleCopyEffect: $btnOptions}),
			),
			new ContextUtil.Action(
				"Upload Pinned List (SHIFT for Add Only)",
				evt => this._sublistManager.pHandleClick_upload({isAdditive: evt.shiftKey}),
			),
		];

		// if (opts.sendToBrew) {
		// 	if (contextOptions.length) contextOptions.push(null); // Add a spacer after the previous group
		//
		// 	const action = new ContextUtil.Action(
		// 		"Edit in Homebrew Builder",
		// 		() => {
		// 			const meta = opts.sendToBrew.fnGetMeta();
		// 			const toLoadData = [meta.page, meta.source, meta.hash];
		// 			window.location = `${UrlUtil.PG_MAKE_BREW}#${opts.sendToBrew.mode.toUrlified()}${HASH_PART_SEP}${UrlUtil.packSubHash("statemeta", toLoadData)}`;
		// 		},
		// 	);
		// 	contextOptions.push(action);
		// }

		if (opts.other?.length) {
			if (contextOptions.length) contextOptions.push(null); // Add a spacer after the previous group

			opts.other.forEach(oth => {
				const action = oth.type === "link"
					? new ContextUtil.ActionLink(
						oth.name,
						oth.fn,
					)
					: new ContextUtil.Action(
						oth.name,
						oth.pFn,
					);
				contextOptions.push(action);
			});
		}

		const menu = ContextUtil.getMenu(contextOptions);
		$btnOptions
			.off("click")
			.on("click", evt => ContextUtil.pOpenMenu(evt, menu));
	}

	async _handleGenericContextMenuClick_pDoMassPopout (evt, ele, selection) {
		const entities = selection.map(listItem => ({entity: this._dataList[listItem.ix], hash: listItem.values.hash}));
		return _UtilListPage.pDoMassPopout(evt, ele, entities);
	}

	doDeselectAll () { this.primaryLists.forEach(list => list.deselectAll()); }

	async pDoLoadHash (id, {lockToken} = {}) {
		try {
			lockToken = await this._lockHashchange.pLock({token: lockToken});
			this._lastRender.entity = this._dataList[id];
			return (await this._pDoLoadHash({id, lockToken}));
		} finally {
			this._lockHashchange.unlock();
		}
	}

	getListItem () { throw new Error(`Unimplemented!`); }
	pHandleUnknownHash () { throw new Error(`Unimplemented!`); }

	async pDoLoadSubHash (sub, {lockToken} = {}) {
		try {
			lockToken = await this._lockHashchange.pLock({token: lockToken});
			return (await this._pDoLoadSubHash({sub, lockToken}));
		} finally {
			this._lockHashchange.unlock();
		}
	}

	/* -------------------------------------------- */

	handleFilterChange () {
		const f = this._filterBox.getValues();
		this._list.filter(item => this._pageFilter.toDisplay(f, this._dataList[item.ix]));
		FilterBox.selectFirstVisible(this._dataList);
	}

	/* -------------------------------------------- */

	_tabTitleStats = "Traits";

	async _pDoLoadHash ({id, lockToken}) {
		this._$pgContent.empty();

		this._renderer.setFirstSection(true);
		const ent = this._dataList[id];

		const tabMetaStats = new Renderer.utils.TabButton({
			label: this._tabTitleStats,
			fnChange: this._renderStats_onTabChangeStats.bind(this),
			fnPopulate: this._renderStats_doBuildStatsTab.bind(this, {ent}),
			isVisible: true,
		});

		const tabMetasAdditional = this._renderStats_getTabMetasAdditional({ent});

		Renderer.utils.bindTabButtons({
			tabButtons: [tabMetaStats, ...tabMetasAdditional].filter(it => it.isVisible),
			tabLabelReference: [tabMetaStats, ...tabMetasAdditional].map(it => it.label),
			$wrpTabs: this._$wrpTabs,
			$pgContent: this._$pgContent,
		});

		this._updateSelected();
	}

	async _pPreloadSublistSources (json) { /* Implement as required */ }

	async _pDoLoadSubHash ({sub, lockToken}) {
		if (this._filterBox) sub = this._filterBox.setFromSubHashes(sub);
		if (this._sublistManager) sub = await this._sublistManager.pSetFromSubHashes(sub, this._pPreloadSublistSources.bind(this));
		if (this._bookView) sub = await this._bookView.pHandleSub(sub);
		return sub;
	}

	_renderStats_getTabMetasAdditional ({ent}) { return []; }

	_renderStats_onTabChangeStats () { /* Implement as required. */ }

	/** @abstract */
	_renderStats_doBuildStatsTab ({ent}) { throw new Error("Unimplemented!"); }
}

class ListPageBookView extends BookModeViewBase {
	_hashKey = "printview";
	_hasPrintColumns = true;

	constructor (
		{
			sublistManager,
			fnGetEntLastLoaded,
			pageTitle,
			namePlural,
			fnPartition = null,
			...rest
		},
	) {
		super({...rest});
		this._sublistManager = sublistManager;
		this._fnGetEntLastLoaded = fnGetEntLastLoaded;
		this._pageTitle = pageTitle;
		this._namePlural = namePlural;
		this._fnPartition = fnPartition;

		this._bookViewToShow = null;
	}

	_$getEleNoneVisible () {
		return $$`<div class="w-100 ve-flex-col ve-flex-h-center no-shrink no-print mb-3 mt-auto">
			<div class="mb-2 ve-flex-vh-center min-h-0">
				<span class="initial-message">If you wish to view multiple ${this._namePlural}, please first make a list</span>
			</div>
			<div class="ve-flex-vh-center">${this._$getBtnNoneVisibleClose()}</div>
		</div>`;
	}

	async _$pGetWrpControls ({$wrpContent}) {
		const out = await super._$pGetWrpControls({$wrpContent});
		const {$wrpPrint} = out;
		return out;
	}

	async _pGetRenderContentMeta ({$wrpContent, $wrpContentOuter}) {
		$wrpContent.addClass("p-2");

		this._bookViewToShow = this._sublistManager.getSublistedEntities();

		const partitions = [];
		if (this._fnPartition) {
			this._bookViewToShow.forEach(it => {
				const partition = this._fnPartition(it);
				(partitions[partition] = partitions[partition] || []).push(it);
			});
		} else partitions[0] = this._bookViewToShow;

		const stack = partitions
			.filter(Boolean)
			.flatMap(arr => arr.map(ent => this._getRenderedEnt(ent)));

		if (!this._bookViewToShow.length && Hist.lastLoadedId != null) {
			stack.push(this._getRenderedEnt(this._fnGetEntLastLoaded()));
		}

		$wrpContent.append(stack.join(""));

		return {
			cntSelectedEnts: this._bookViewToShow.length,
			isAnyEntityRendered: !!stack.length,
		};
	}

	_getRenderedEnt (ent) {
		return `<div class="bkmv__wrp-item ve-inline-block print__ve-block print__my-2">
			<table class="w-100 stats stats--book stats--bkmv"><tbody>
			${Renderer.hover.getFnRenderCompact(UrlUtil.getCurrentPage(), {isStatic: true})(ent)}
			</tbody></table>
		</div>`;
	}

	_getSorted (a, b) {
		return SortUtil.ascSortLower(a.name, b.name);
	}
}
