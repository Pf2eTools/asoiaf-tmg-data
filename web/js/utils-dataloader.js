"use strict";

/**
 * General notes:
 *  - Raw/`raw_` data *should* be left as-is from `DataUtil`, such that we match anything returned by a prop-specific
 *    `.loadRawJSON` in `DataUtil`. Note that this is generally *not* the same as the result of `DataUtil.loadRawJSON`,
 *    which is instead JSON prior to the application of `_copy`/etc.!
 *  - Other cached data (without `raw_`) should be ready for use, with all references resolved to the best of our
 *    capabilities.
 */

// region Utilities

class _DataLoaderConst {
	static SOURCE_SITE_ALL = Symbol("SOURCE_SITE_ALL");
	static SOURCE_PRERELEASE_ALL_CURRENT = Symbol("SOURCE_PRERELEASE_ALL_CURRENT");
	static SOURCE_BREW_ALL_CURRENT = Symbol("SOURCE_BREW_ALL_CURRENT");

	static ENTITY_NULL = Symbol("ENTITY_NULL");

	static _SOURCES_ALL_NON_SITE = new Set([
		this.SOURCE_PRERELEASE_ALL_CURRENT,
		this.SOURCE_BREW_ALL_CURRENT,
	]);

	static isSourceAllNonSite (source) {
		return this._SOURCES_ALL_NON_SITE.has(source);
	}
}

class _DataLoaderInternalUtil {
	static getCleanPageSourceHash ({page, source, hash}) {
		return {
			page: this.getCleanPage({page}),
			source: this.getCleanSource({source}),
			hash: this.getCleanHash({hash}),
		};
	}

	static getCleanPage ({page}) { return page.toLowerCase(); }
	static getCleanSource ({source}) { return source.toLowerCase(); }
	static getCleanHash ({hash}) { return hash.toLowerCase(); }

	/* -------------------------------------------- */

	static getCleanPageFluff ({page}) { return `${this.getCleanPage({page})}fluff`; }

	/* -------------------------------------------- */

	static _NOTIFIED_FAILED_DEREFERENCES = new Set();

	static doNotifyFailedDereferences ({missingRefSets, diagnostics}) {
		// region Avoid repeatedly throwing errors for the same missing references
		const missingRefSetsUnseen = Object.entries(missingRefSets)
			.mergeMap(([prop, set]) => ({
				[prop]: new Set(
					[...set]
						.filter(ref => {
							const refLower = ref.toLowerCase();
							const out = !this._NOTIFIED_FAILED_DEREFERENCES.has(refLower);
							this._NOTIFIED_FAILED_DEREFERENCES.add(refLower);
							return out;
						}),
				),
			}));
		// endregion

		const cntMissingRefs = Object.values(missingRefSetsUnseen).map(({size}) => size).sum();
		if (!cntMissingRefs) return;

		const notificationRefs = Object.entries(missingRefSetsUnseen)
			.map(([k, v]) => `${k}: ${[...v].sort(SortUtil.ascSortLower).join(", ")}`)
			.join("; ");

		const ptDiagnostics = DataLoader.getDiagnosticsSummary(diagnostics);
		const msgStart = `Failed to load references for ${cntMissingRefs} entr${cntMissingRefs === 1 ? "y" : "ies"}!`;

		JqueryUtil.doToast({
			type: "danger",
			content: `${msgStart} Reference types and values were: ${[notificationRefs, ptDiagnostics].join(" ")}`,
			isAutoHide: false,
		});

		const cnslRefs = [
			...Object.entries(missingRefSetsUnseen)
				.map(([k, v]) => `${k}:\n\t${[...v].sort(SortUtil.ascSortLower).join("\n\t")}`),
			ptDiagnostics,
		]
			.filter(Boolean)
			.join("\n");

		setTimeout(() => { throw new Error(`${msgStart}\nReference types and values were:\n${cnslRefs}`); });
	}
}

// endregion

/* -------------------------------------------- */

// region Cache

class _DataLoaderCache {
	static _PARTITION_UNKNOWN = 0;
	static _PARTITION_SITE = 1;
	static _PARTITION_PRERELEASE = 2;
	static _PARTITION_BREW = 3;

	_cache = {};
	_cacheSiteLists = {};
	_cachePrereleaseLists = {};
	_cacheBrewLists = {};

	get (pageClean, sourceClean, hashClean) {
		return this._cache[pageClean]?.[sourceClean]?.[hashClean];
	}

	getAllSite (pageClean) {
		return Object.values(this._cacheSiteLists[pageClean] || {});
	}

	getAllPrerelease (pageClean) {
		return Object.values(this._cachePrereleaseLists[pageClean] || {});
	}

	getAllBrew (pageClean) {
		return Object.values(this._cacheBrewLists[pageClean] || {});
	}

	set (pageClean, sourceClean, hashClean, ent) {
		// region Set primary cache
		let pageCache = this._cache[pageClean];
		if (!pageCache) {
			pageCache = {};
			this._cache[pageClean] = pageCache;
		}

		let sourceCache = pageCache[sourceClean];
		if (!sourceCache) {
			sourceCache = {};
			pageCache[sourceClean] = sourceCache;
		}

		sourceCache[hashClean] = ent;
		// endregion

		if (ent === _DataLoaderConst.ENTITY_NULL) return;

		// region Set site/prerelease/brew list cache
		switch (this._set_getPartition(ent)) {
			case this.constructor._PARTITION_SITE: {
				return this._set_addToPartition({
					cache: this._cacheSiteLists,
					pageClean,
					hashClean,
					ent,
				});
			}

			case this.constructor._PARTITION_PRERELEASE: {
				return this._set_addToPartition({
					cache: this._cachePrereleaseLists,
					pageClean,
					hashClean,
					ent,
				});
			}

			case this.constructor._PARTITION_BREW: {
				return this._set_addToPartition({
					cache: this._cacheBrewLists,
					pageClean,
					hashClean,
					ent,
				});
			}

			// Skip by default
		}
		// endregion
	}

	_set_getPartition (ent) {
		if (ent.adventure) return this._set_getPartition_fromSource(SourceUtil.getEntitySource(ent.adventure));
		if (ent.book) return this._set_getPartition_fromSource(SourceUtil.getEntitySource(ent.book));

		if (ent.__prop !== "item" || ent._category !== "Specific Variant") return this._set_getPartition_fromSource(SourceUtil.getEntitySource(ent));

		// "Specific Variant" items have a dual source. For the purposes of partitioning:
		//   - only items with both `baseitem` source and `magicvariant` source both "site" sources
		//   - items which include any brew are treated as brew
		//   - items which include any prerelease (and no brew) are treated as prerelease
		const entitySource = SourceUtil.getEntitySource(ent);
		const partitionBaseitem = this._set_getPartition_fromSource(entitySource);
		const partitionMagicvariant = this._set_getPartition_fromSource(ent._baseSource ?? entitySource);

		if (partitionBaseitem === partitionMagicvariant && partitionBaseitem === this.constructor._PARTITION_SITE) return this.constructor._PARTITION_SITE;
		if (partitionBaseitem === this.constructor._PARTITION_BREW || partitionMagicvariant === this.constructor._PARTITION_BREW) return this.constructor._PARTITION_BREW;
		return this.constructor._PARTITION_PRERELEASE;
	}

	_set_getPartition_fromSource (partitionSource) {
		if (SourceUtil.isSiteSource(partitionSource)) return this.constructor._PARTITION_SITE;
		if (PrereleaseUtil.hasSourceJson(partitionSource)) return this.constructor._PARTITION_PRERELEASE;
		if (BrewUtil2.hasSourceJson(partitionSource)) return this.constructor._PARTITION_BREW;
		return this.constructor._PARTITION_UNKNOWN;
	}

	_set_addToPartition ({cache, pageClean, hashClean, ent}) {
		let siteListCache = cache[pageClean];
		if (!siteListCache) {
			siteListCache = {};
			cache[pageClean] = siteListCache;
		}
		siteListCache[hashClean] = ent;
	}
}

// endregion

/* -------------------------------------------- */

// region Data type loading

class _DataTypeLoader {
	static PROPS = [];
	static PAGE = null;
	static IS_FLUFF = false;

	static register ({fnRegister}) {
		fnRegister({
			loader: new this(),
			props: this.PROPS,
			page: this.PAGE,
			isFluff: this.IS_FLUFF,
		});
	}

	static _getAsRawPrefixed (json, {propsRaw}) {
		return {
			...propsRaw.mergeMap(prop => ({[`raw_${prop}`]: json[prop]})),
		};
	}

	/* -------------------------------------------- */

	/** Used to reduce phase 1 caching for a loader where phase 2 is the primary caching step. */
	phase1CachePropAllowlist;

	/** (Unused) */
	phase2CachePropAllowlist;

	hasPhase2Cache = false;

	_cache_pSiteData = {};
	_cache_pPostCaches = {};

	/**
	 * @param pageClean
	 * @param sourceClean
	 * @return {string}
	 */
	_getSiteIdent ({pageClean, sourceClean}) { throw new Error("Unimplemented!"); }

	_isPrereleaseAvailable () { return typeof PrereleaseUtil !== "undefined"; }

	_isBrewAvailable () { return typeof BrewUtil2 !== "undefined"; }

	async _pPrePopulate ({data, isPrerelease, isBrew}) { /* Implement as required */ }

	async pGetSiteData ({pageClean, sourceClean}) {
		if (_DataLoaderConst.isSourceAllNonSite(sourceClean)) return {};
		const propCache = this._getSiteIdent({pageClean, sourceClean});
		this._cache_pSiteData[propCache] = this._cache_pSiteData[propCache] || this._pGetSiteData({pageClean, sourceClean});
		return this._cache_pSiteData[propCache];
	}

	async _pGetSiteData ({pageClean, sourceClean}) { throw new Error("Unimplemented!"); }

	async pGetStoredPrereleaseData () {
		if (!this._isPrereleaseAvailable()) return {};
		return this._pGetStoredPrereleaseData();
	}

	async pGetStoredBrewData () {
		if (!this._isBrewAvailable()) return {};
		return this._pGetStoredBrewData();
	}

	async _pGetStoredPrereleaseData () {
		return this._pGetStoredPrereleaseBrewData({brewUtil: PrereleaseUtil, isPrerelease: true});
	}

	async _pGetStoredBrewData () {
		return this._pGetStoredPrereleaseBrewData({brewUtil: BrewUtil2, isBrew: true});
	}

	async _pGetStoredPrereleaseBrewData ({brewUtil, isPrerelease, isBrew}) {
		const prereleaseBrewData = await brewUtil.pGetBrewProcessed();
		await this._pPrePopulate({data: prereleaseBrewData, isPrerelease, isBrew});
		return prereleaseBrewData;
	}

	async pGetPostCacheData ({siteData = null, prereleaseData = null, brewData = null, lockToken2}) { /* Implement as required */ }

	async _pGetPostCacheData_obj_withCache ({obj, propCache, lockToken2}) {
		this._cache_pPostCaches[propCache] = this._cache_pPostCaches[propCache] || this._pGetPostCacheData_obj({obj, lockToken2});
		return this._cache_pPostCaches[propCache];
	}

	async _pGetPostCacheData_obj ({obj, lockToken2}) { throw new Error("Unimplemented!"); }

	hasCustomCacheStrategy ({obj}) { return false; }

	addToCacheCustom ({cache, obj}) { /* Implement as required */ }
}

class _DataTypeLoaderMultiSource extends _DataTypeLoader {
	_prop;

	_getSiteIdent ({pageClean, sourceClean}) {
		// use `.toString()` in case `sourceClean` is a `Symbol`
		return `${this._prop}__${sourceClean.toString()}`;
	}

	async _pGetSiteData ({pageClean, sourceClean}) {
		const data = await this._pGetSiteData_data({sourceClean});

		if (data == null) return {};

		await this._pPrePopulate({data});

		return data;
	}

	async _pGetSiteData_data ({sourceClean}) {
		if (sourceClean === _DataLoaderConst.SOURCE_SITE_ALL) return this._pGetSiteDataAll();

		const source = Parser.sourceJsonToJson(sourceClean);
		return DataUtil[this._prop].pLoadSingleSource(source);
	}

	async _pGetSiteDataAll () {
		return DataUtil[this._prop].loadJSON();
	}
}


class _DataTypeLoaderSong extends _DataTypeLoaderMultiSource {
	static PROPS = [...UrlUtil.PAGE_TO_PROPS[UrlUtil.PG_SONG]];
	static PAGE = UrlUtil.PG_SONG;

	_prop = "song";

	async _pPrePopulate ({data, isPrerelease, isBrew}) {
	}
}

// endregion

/* -------------------------------------------- */

// region Data loader

class DataLoader {
	static _PROP_TO_HASH_PAGE = {
		"song": UrlUtil.PG_SONG,
		"attachment": UrlUtil.PG_SONG,
		"unit": UrlUtil.PG_SONG,
		"ncu": UrlUtil.PG_SONG,
		"special": UrlUtil.PG_SONG,
		"tactics": UrlUtil.PG_SONG,
	};

	static _DATA_TYPE_LOADERS = {};
	static _DATA_TYPE_LOADER_LIST = [];

	static _init () {
		this._registerPropToHashPages();
		this._registerDataTypeLoaders();
		return null;
	}

	static _registerPropToHashPages () {
		Object.entries(this._PROP_TO_HASH_PAGE)
			.forEach(([k, v]) => this._PROP_TO_HASH_PAGE[`${k}Fluff`] = _DataLoaderInternalUtil.getCleanPageFluff({page: v}));
	}

	static _registerDataTypeLoader ({loader, props, page, isFluff}) {
		this._DATA_TYPE_LOADER_LIST.push(loader);

		if (!props?.length) throw new Error(`No "props" specified for loader "${loader.constructor.name}"!`);

		props.forEach(prop => this._DATA_TYPE_LOADERS[_DataLoaderInternalUtil.getCleanPage({page: prop})] = loader);

		if (!page) return;

		this._DATA_TYPE_LOADERS[
			isFluff
				? _DataLoaderInternalUtil.getCleanPageFluff({page})
				: _DataLoaderInternalUtil.getCleanPage({page})
		] = loader;
	}

	static _registerDataTypeLoaders () {
		const fnRegister = this._registerDataTypeLoader.bind(this);

		_DataTypeLoaderSong.register({fnRegister});
	}

	static _ = this._init();

	static _CACHE = new _DataLoaderCache();
	static _LOCK_1 = new VeLock({isDbg: false, name: "loader-lock-1"});
	static _LOCK_2 = new VeLock({isDbg: false, name: "loader-lock-2"});

	/* -------------------------------------------- */

	/**
	 * @param page
	 * @param source
	 * @param hash
	 * @param [isCopy] If a copy, rather than the original entity, should be returned.
	 * @param [isRequired] If an error should be thrown on a missing entity.
	 * @param [_isReturnSentinel] If a null sentinel should be returned, if it exists.
	 * @param [_isInsertSentinelOnMiss] If a null sentinel should be inserted on cache miss.
	 */
	static getFromCache (
		page,
		source,
		hash,
		{
			isCopy = false,
			isRequired = false,
			_isReturnSentinel = false,
			_isInsertSentinelOnMiss = false,
		} = {},
	) {
		const {page: pageClean, source: sourceClean, hash: hashClean} = _DataLoaderInternalUtil.getCleanPageSourceHash({page, source, hash});
		const ent = this._getFromCache({pageClean, sourceClean, hashClean, isCopy, _isReturnSentinel, _isInsertSentinelOnMiss});
		return this._getVerifiedRequiredEntity({pageClean, sourceClean, hashClean, ent, isRequired});
	}

	static _getFromCache (
		{
			pageClean,
			sourceClean,
			hashClean,
			isCopy = false,
			_isInsertSentinelOnMiss = false,
			_isReturnSentinel = false,
		},
	) {
		const out = this._CACHE.get(pageClean, sourceClean, hashClean);

		if (out === _DataLoaderConst.ENTITY_NULL) {
			if (_isReturnSentinel) return out;
			if (!_isReturnSentinel) return null;
		}

		if (out == null && _isInsertSentinelOnMiss) {
			this._CACHE.set(pageClean, sourceClean, hashClean, _DataLoaderConst.ENTITY_NULL);
		}

		if (!isCopy || out == null) return out;
		return MiscUtil.copyFast(out);
	}

	/* -------------------------------------------- */

	static _getVerifiedRequiredEntity ({pageClean, sourceClean, hashClean, ent, isRequired}) {
		if (ent || !isRequired) return ent;
		throw new Error(`Could not find entity for page/prop "${pageClean}" with source "${sourceClean}" and hash "${hashClean}"`);
	}

	/* -------------------------------------------- */

	static async pCacheAndGetAllSite (page, {isSilent = false} = {}) {
		const pageClean = _DataLoaderInternalUtil.getCleanPage({page});

		if (this._PAGES_NO_CONTENT.has(pageClean)) return null;

		const dataLoader = this._pCache_getDataTypeLoader({pageClean, isSilent});
		if (!dataLoader) return null;

		// (Avoid preloading missing brew here, as we only return site data.)

		const {siteData} = await this._pCacheAndGet_getCacheMeta({pageClean, sourceClean: _DataLoaderConst.SOURCE_SITE_ALL, dataLoader});
		await this._pCacheAndGet_processCacheMeta({dataLoader, siteData});

		return this._CACHE.getAllSite(pageClean);
	}

	static async pCacheAndGetAllPrerelease (page, {isSilent = false} = {}) {
		return this._CacheAndGetAllPrerelease.pCacheAndGetAll({parent: this, page, isSilent});
	}

	static async pCacheAndGetAllBrew (page, {isSilent = false} = {}) {
		return this._CacheAndGetAllBrew.pCacheAndGetAll({parent: this, page, isSilent});
	}

	static _CacheAndGetAllPrereleaseBrew = class {
		static _SOURCE_ALL;
		static _PROP_DATA;

		static async pCacheAndGetAll (
			{
				parent,
				page,
				isSilent,
			},
		) {
			const pageClean = _DataLoaderInternalUtil.getCleanPage({page});

			if (parent._PAGES_NO_CONTENT.has(pageClean)) return null;

			const dataLoader = parent._pCache_getDataTypeLoader({pageClean, isSilent});
			if (!dataLoader) return null;

			// (Avoid preloading missing prerelease/homebrew here, as we only return currently-loaded prerelease/homebrew.)

			const cacheMeta = await parent._pCacheAndGet_getCacheMeta({pageClean, sourceClean: this._SOURCE_ALL, dataLoader});
			await parent._pCacheAndGet_processCacheMeta({dataLoader, [this._PROP_DATA]: cacheMeta[this._PROP_DATA]});

			return this._getAllCached({parent, pageClean});
		}

		/** @abstract */
		static _getAllCached ({parent, pageClean}) { throw new Error("Unimplemented!"); }
	};

	static _CacheAndGetAllPrerelease = class extends this._CacheAndGetAllPrereleaseBrew {
		static _SOURCE_ALL = _DataLoaderConst.SOURCE_PRERELEASE_ALL_CURRENT;
		static _PROP_DATA = "prereleaseData";

		static _getAllCached ({parent, pageClean}) { return parent._CACHE.getAllPrerelease(pageClean); }
	};

	static _CacheAndGetAllBrew = class extends this._CacheAndGetAllPrereleaseBrew {
		static _SOURCE_ALL = _DataLoaderConst.SOURCE_BREW_ALL_CURRENT;
		static _PROP_DATA = "brewData";

		static _getAllCached ({parent, pageClean}) { return parent._CACHE.getAllBrew(pageClean); }
	};

	/* -------------------------------------------- */

	static _PAGES_NO_CONTENT = new Set([
		_DataLoaderInternalUtil.getCleanPage({page: "generic"}),
		_DataLoaderInternalUtil.getCleanPage({page: "hover"}),
	]);

	/**
	 * @param page
	 * @param source
	 * @param hash
	 * @param [isCopy] If a copy, rather than the original entity, should be returned.
	 * @param [isRequired] If an error should be thrown on a missing entity.
	 * @param [isSilent] If errors should not be thrown on a missing implementation.
	 * @param [lockToken2] Post-process lock token for recursive calls.
	 */
	static async pCacheAndGet (page, source, hash, {isCopy = false, isRequired = false, isSilent = false, lockToken2} = {}) {
		const fromCache = this.getFromCache(page, source, hash, {isCopy, _isReturnSentinel: true});
		if (fromCache === _DataLoaderConst.ENTITY_NULL) return null;
		if (fromCache) return fromCache;

		const {page: pageClean, source: sourceClean, hash: hashClean} = _DataLoaderInternalUtil.getCleanPageSourceHash({page, source, hash});

		if (this._PAGES_NO_CONTENT.has(pageClean)) return this._getVerifiedRequiredEntity({pageClean, sourceClean, hashClean, ent: null, isRequired});

		const dataLoader = this._pCache_getDataTypeLoader({pageClean, isSilent});
		if (!dataLoader) return this._getVerifiedRequiredEntity({pageClean, sourceClean, hashClean, ent: null, isRequired});

		const isUnavailablePrerelease = await this._PrereleasePreloader._pPreloadMissing({parent: this, sourceClean});
		if (isUnavailablePrerelease) return this._getVerifiedRequiredEntity({pageClean, sourceClean, hashClean, ent: null, isRequired});

		const isUnavailableBrew = await this._BrewPreloader._pPreloadMissing({parent: this, sourceClean});
		if (isUnavailableBrew) return this._getVerifiedRequiredEntity({pageClean, sourceClean, hashClean, ent: null, isRequired});

		const {siteData = null, prereleaseData = null, brewData = null} = await this._pCacheAndGet_getCacheMeta({pageClean, sourceClean, dataLoader});
		await this._pCacheAndGet_processCacheMeta({dataLoader, siteData, prereleaseData, brewData, lockToken2});

		return this.getFromCache(page, source, hash, {isCopy, _isInsertSentinelOnMiss: true});
	}

	static async pCacheAndGetHash (page, hash, opts) {
		const source = UrlUtil.decodeHash(hash).last();
		return DataLoader.pCacheAndGet(page, source, hash, opts);
	}

	static _PrereleaseBrewPreloader = class {
		static _LOCK_0;
		static _SOURCES_ATTEMPTED;
		/** Cache of clean (lowercase) source -> URL. */
		static _CACHE_SOURCE_CLEAN_TO_URL;
		static _SOURCE_ALL;

		/**
		 * Phase 0: check if prerelease/homebrew, and if so, check/load the source (if available).
		 *   Track failures (i.e., there is no available JSON for the source requested), and skip repeated failures.
		 *   This allows us to avoid an expensive mass re-cache, if a source which does not exist is requested for
		 *   loading multiple times.
		 */
		static async pPreloadMissing ({parent, sourceClean}) {
			try {
				await this._LOCK_0.pLock();
				return (await this._pPreloadMissing({parent, sourceClean}));
			} finally {
				this._LOCK_0.unlock();
			}
		}

		/**
		 * @param parent
		 * @param sourceClean
		 * @return {Promise<boolean>} `true` if the source does not exist and could not be loaded, false otherwise.
		 */
		static async _pPreloadMissing ({parent, sourceClean}) {
			if (this._isExistingMiss({parent, sourceClean})) return true;

			if (!this._isPossibleSource({parent, sourceClean})) return false;
			if (sourceClean === this._SOURCE_ALL) return false;

			const brewUtil = this._getBrewUtil();
			if (!brewUtil) {
				this._setExistingMiss({parent, sourceClean});
				return true;
			}

			if (brewUtil.hasSourceJson(sourceClean)) return false;

			const urlBrew = await this._pGetSourceUrl({parent, sourceClean});
			if (!urlBrew) {
				this._setExistingMiss({parent, sourceClean});
				return true;
			}

			await brewUtil.pAddBrewFromUrl(urlBrew);
			return false;
		}

		static _isExistingMiss ({sourceClean}) {
			return this._SOURCES_ATTEMPTED.has(sourceClean);
		}

		static _setExistingMiss ({sourceClean}) {
			this._SOURCES_ATTEMPTED.add(sourceClean);
		}

		/* -------------------------------------------- */

		static async _pInitCacheSourceToUrl () {
			if (this._CACHE_SOURCE_CLEAN_TO_URL) return;

			const index = await this._pGetUrlIndex();
			if (!index) return this._CACHE_SOURCE_CLEAN_TO_URL = {};

			const brewUtil = this._getBrewUtil();
			const urlRoot = await brewUtil.pGetCustomUrl();

			this._CACHE_SOURCE_CLEAN_TO_URL = Object.entries(index)
				.mergeMap(([src, url]) => ({[_DataLoaderInternalUtil.getCleanSource({source: src})]: brewUtil.getFileUrl(url, urlRoot)}));
		}

		static async _pGetUrlIndex () {
			try {
				return (await this._pGetSourceIndex());
			} catch (e) {
				setTimeout(() => { throw e; });
				return null;
			}
		}

		static async _pGetSourceUrl ({sourceClean}) {
			await this._pInitCacheSourceToUrl();
			return this._CACHE_SOURCE_CLEAN_TO_URL[sourceClean];
		}

		/** @abstract */
		static _isPossibleSource ({parent, sourceClean}) { throw new Error("Unimplemented!"); }
		/** @abstract */
		static _getBrewUtil () { throw new Error("Unimplemented!"); }
		/** @abstract */
		static _pGetSourceIndex () { throw new Error("Unimplemented!"); }
	};

	static _PrereleasePreloader = class extends this._PrereleaseBrewPreloader {
		static _LOCK_0 = new VeLock({isDbg: false, name: "loader-lock-0--prerelease"});
		static _SOURCE_ALL = _DataLoaderConst.SOURCE_BREW_ALL_CURRENT;
		static _SOURCES_ATTEMPTED = new Set();
		static _CACHE_SOURCE_CLEAN_TO_URL = null;

		static _isPossibleSource ({parent, sourceClean}) { return parent._isPrereleaseSource({sourceClean}) && !Parser.SOURCE_JSON_TO_FULL[Parser.sourceJsonToJson(sourceClean)]; }
		static _getBrewUtil () { return typeof PrereleaseUtil !== "undefined" ? PrereleaseUtil : null; }
		static async _pGetSourceIndex () { return DataUtil.prerelease.pLoadSourceIndex(await PrereleaseUtil.pGetCustomUrl()); }
	};

	static _BrewPreloader = class extends this._PrereleaseBrewPreloader {
		static _LOCK_0 = new VeLock({isDbg: false, name: "loader-lock-0--brew"});
		static _SOURCE_ALL = _DataLoaderConst.SOURCE_PRERELEASE_ALL_CURRENT;
		static _SOURCES_ATTEMPTED = new Set();
		static _CACHE_SOURCE_CLEAN_TO_URL = null;

		static _isPossibleSource ({parent, sourceClean}) { return !parent._isSiteSource({sourceClean}) && !parent._isPrereleaseSource({sourceClean}); }
		static _getBrewUtil () { return typeof BrewUtil2 !== "undefined" ? BrewUtil2 : null; }
		static async _pGetSourceIndex () { return DataUtil.brew.pLoadSourceIndex(await BrewUtil2.pGetCustomUrl()); }
	};

	static async _pCacheAndGet_getCacheMeta ({pageClean, sourceClean, dataLoader}) {
		try {
			await this._LOCK_1.pLock();
			return (await this._pCache({pageClean, sourceClean, dataLoader}));
		} finally {
			this._LOCK_1.unlock();
		}
	}

	static async _pCache ({pageClean, sourceClean, dataLoader}) {
		// region Fetch from site data
		const siteData = await dataLoader.pGetSiteData({pageClean, sourceClean});
		this._pCache_addToCache({allDataMerged: siteData, propAllowlist: dataLoader.phase1CachePropAllowlist || new Set(dataLoader.constructor.PROPS)});
		// Always early-exit, regardless of whether the entity was found in the cache, if we know this is a site source
		if (this._isSiteSource({sourceClean})) return {siteData};
		// endregion

		const out = {siteData};

		// region Fetch from already-stored prerelease/brew data
		//   As we have preloaded missing prerelease/brew earlier in the flow, we know that a prerelease/brew is either
		//   present, or unavailable
		if (typeof PrereleaseUtil !== "undefined") {
			const prereleaseData = await dataLoader.pGetStoredPrereleaseData();
			this._pCache_addToCache({allDataMerged: prereleaseData, propAllowlist: dataLoader.phase1CachePropAllowlist || new Set(dataLoader.constructor.PROPS)});
			out.prereleaseData = prereleaseData;
		}

		if (typeof BrewUtil2 !== "undefined") {
			const brewData = await dataLoader.pGetStoredBrewData();
			this._pCache_addToCache({allDataMerged: brewData, propAllowlist: dataLoader.phase1CachePropAllowlist || new Set(dataLoader.constructor.PROPS)});
			out.brewData = brewData;
		}
		// endregion

		return out;
	}

	static async _pCacheAndGet_processCacheMeta ({dataLoader, siteData = null, prereleaseData = null, brewData = null, lockToken2 = null}) {
		if (!dataLoader.hasPhase2Cache) return;

		try {
			lockToken2 = await this._LOCK_2.pLock({token: lockToken2});
			await this._pCacheAndGet_processCacheMeta_({dataLoader, siteData, prereleaseData, brewData, lockToken2});
		} finally {
			this._LOCK_2.unlock();
		}
	}

	static async _pCacheAndGet_processCacheMeta_ ({dataLoader, siteData = null, prereleaseData = null, brewData = null, lockToken2 = null}) {
		const {siteDataPostCache, prereleaseDataPostCache, brewDataPostCache} = await dataLoader.pGetPostCacheData({siteData, prereleaseData, brewData, lockToken2});

		this._pCache_addToCache({allDataMerged: siteDataPostCache, propAllowlist: dataLoader.phase2CachePropAllowlist || new Set(dataLoader.constructor.PROPS)});
		this._pCache_addToCache({allDataMerged: prereleaseDataPostCache, propAllowlist: dataLoader.phase2CachePropAllowlist || new Set(dataLoader.constructor.PROPS)});
		this._pCache_addToCache({allDataMerged: brewDataPostCache, propAllowlist: dataLoader.phase2CachePropAllowlist || new Set(dataLoader.constructor.PROPS)});
	}

	static _pCache_getDataTypeLoader ({pageClean, isSilent}) {
		const dataLoader = this._DATA_TYPE_LOADERS[pageClean];
		if (!dataLoader && !isSilent) throw new Error(`No loading strategy found for page "${pageClean}"!`);
		return dataLoader;
	}

	static _pCache_addToCache ({allDataMerged, propAllowlist}) {
		if (!allDataMerged) return;

		allDataMerged = {...allDataMerged};

		this._DATA_TYPE_LOADER_LIST
			.filter(loader => loader.hasCustomCacheStrategy({obj: allDataMerged}))
			.forEach(loader => {
				const propsToRemove = loader.addToCacheCustom({cache: this._CACHE, obj: allDataMerged});
				propsToRemove.forEach(prop => delete allDataMerged[prop]);
			});

		Object.keys(allDataMerged)
			.forEach(prop => {
				if (!propAllowlist.has(prop)) return;

				const arr = allDataMerged[prop];
				if (!arr?.length || !(arr instanceof Array)) return;

				const hashBuilder = UrlUtil.URL_TO_HASH_BUILDER[prop];
				if (!hashBuilder) return;

				arr.forEach(ent => {
					this._pCache_addEntityToCache({prop, hashBuilder, ent});
					DataUtil.proxy.getVersions(prop, ent)
						.forEach(entVer => this._pCache_addEntityToCache({prop, hashBuilder, ent: entVer}));
				});
			});
	}

	static _pCache_addEntityToCache ({prop, hashBuilder, ent}) {
		ent.__prop = ent.__prop || prop;

		const page = this._PROP_TO_HASH_PAGE[prop];
		const source = SourceUtil.getEntitySource(ent); //
		const hash = hashBuilder(ent);

		const {page: propClean, source: sourceClean, hash: hashClean} = _DataLoaderInternalUtil.getCleanPageSourceHash({page: prop, source, hash});
		const pageClean = page ? _DataLoaderInternalUtil.getCleanPage({page}) : null;

		this._CACHE.set(propClean, sourceClean, hashClean, ent);
		if (pageClean) this._CACHE.set(pageClean, sourceClean, hashClean, ent);
	}

	/* -------------------------------------------- */

	static _CACHE_SITE_SOURCE_CLEAN = null;

	static _doBuildSourceCaches () {
		this._CACHE_SITE_SOURCE_CLEAN = this._CACHE_SITE_SOURCE_CLEAN || new Set(Object.keys(Parser.SOURCE_JSON_TO_FULL)
			.map(src => _DataLoaderInternalUtil.getCleanSource({source: src})));
	}

	static _isSiteSource ({sourceClean}) {
		if (sourceClean === _DataLoaderConst.SOURCE_SITE_ALL) return true;
		if (sourceClean === _DataLoaderConst.SOURCE_BREW_ALL_CURRENT) return false;
		if (sourceClean === _DataLoaderConst.SOURCE_PRERELEASE_ALL_CURRENT) return false;

		this._doBuildSourceCaches();

		return this._CACHE_SITE_SOURCE_CLEAN.has(sourceClean);
	}

	static _isPrereleaseSource ({sourceClean}) {
		if (sourceClean === _DataLoaderConst.SOURCE_SITE_ALL) return false;
		if (sourceClean === _DataLoaderConst.SOURCE_BREW_ALL_CURRENT) return false;
		if (sourceClean === _DataLoaderConst.SOURCE_PRERELEASE_ALL_CURRENT) return true;

		this._doBuildSourceCaches();

		return false;
	}

	/* -------------------------------------------- */

	static getDiagnosticsSummary (diagnostics) {
		diagnostics = diagnostics.filter(Boolean);
		if (!diagnostics.length) return "";

		const filenames = diagnostics
			.map(it => it.filename)
			.filter(Boolean)
			.unique()
			.sort(SortUtil.ascSortLower);

		if (!filenames.length) return "";

		return `Filename${filenames.length === 1 ? " was" : "s were"}: ${filenames.map(it => `"${it}"`).join("; ")}.`;
	}
}

// endregion

/* -------------------------------------------- */

// region Exports

globalThis.DataLoader = DataLoader;

// endregion
