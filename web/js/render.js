"use strict";

// ENTRY RENDERING =====================================================================================================
/*
 * // EXAMPLE USAGE //
 *
 * const entryRenderer = new Renderer();
 *
 * const topLevelEntry = mydata[0];
 * // prepare an array to hold the string we collect while recursing
 * const textStack = [];
 *
 * // recurse through the entry tree
 * entryRenderer.renderEntries(topLevelEntry, textStack);
 *
 * // render the final product by joining together all the collected strings
 * $("#myElement").html(toDisplay.join(""));
 */
globalThis.Renderer = function () {
	this.wrapperTag = "div";
	this.baseUrl = "";
	this.baseMediaUrls = {};

	if (globalThis.DEPLOYED_IMG_ROOT) {
		this.baseMediaUrls["img"] = globalThis.DEPLOYED_IMG_ROOT;
	}

	this._lazyImages = false;
	this._subVariant = false;
	this._firstSection = true;
	this._isAddHandlers = true;
	this._headerIndex = 1;
	this._tagExportDict = null;
	this._trackTitles = {enabled: false, titles: {}};
	this._enumerateTitlesRel = {enabled: false, titles: {}};
	this._isHeaderIndexIncludeTableCaptions = false;
	this._isHeaderIndexIncludeImageTitles = false;
	this._plugins = {};
	this._fnPostProcess = null;
	this._extraSourceClasses = null;
	this._depthTracker = null;
	this._depthTrackerAdditionalProps = [];
	this._depthTrackerAdditionalPropsInherited = [];
	this._lastDepthTrackerInheritedProps = {};
	this._isInternalLinksDisabled = false;
	this._isPartPageExpandCollapseDisabled = false;
	this._fnsGetStyleClasses = {};

	this.getMediaUrl = function (mediaDir, path) {
		if (Renderer.get().baseMediaUrls[mediaDir]) return `${Renderer.get().baseMediaUrls[mediaDir]}${path}`;
		return `${Renderer.get().baseUrl}${mediaDir}/${path}`;
	};

	/**
	 * Other sections should be prefixed with a vertical divider
	 * @param bool
	 */
	this.setFirstSection = function (bool) { this._firstSection = bool; return this; };

	this.isInternalLinksDisabled = function () { return !!this._isInternalLinksDisabled; };

	this._getEnumeratedTitleRel = function (name) {
		if (this._enumerateTitlesRel.enabled && name) {
			const clean = name.toLowerCase();
			this._enumerateTitlesRel.titles[clean] = this._enumerateTitlesRel.titles[clean] || 0;
			return `data-title-relative-index="${this._enumerateTitlesRel.titles[clean]++}"`;
		} else return "";
	};

	this._handleTrackTitles = function (name, {isTable = false, isImage = false} = {}) {
		if (!this._trackTitles.enabled) return;
		if (isTable && !this._isHeaderIndexIncludeTableCaptions) return;
		if (isImage && !this._isHeaderIndexIncludeImageTitles) return;
		this._trackTitles.titles[this._headerIndex] = name;
	};

	this._handleTrackDepth = function (entry, depth) {
		if (!entry.name || !this._depthTracker) return;

		this._lastDepthTrackerInheritedProps = MiscUtil.copyFast(this._lastDepthTrackerInheritedProps);
		if (entry.source) this._lastDepthTrackerInheritedProps.source = entry.source;
		if (this._depthTrackerAdditionalPropsInherited?.length) {
			this._depthTrackerAdditionalPropsInherited.forEach(prop => this._lastDepthTrackerInheritedProps[prop] = entry[prop] || this._lastDepthTrackerInheritedProps[prop]);
		}

		const additionalData = this._depthTrackerAdditionalProps.length
			? this._depthTrackerAdditionalProps.mergeMap(it => ({[it]: entry[it]}))
			: {};

		this._depthTracker.push({
			...this._lastDepthTrackerInheritedProps,
			...additionalData,
			depth,
			name: entry.name,
			type: entry.type,
			ixHeader: this._headerIndex,
			source: this._lastDepthTrackerInheritedProps.source,
			data: entry.data,
			page: entry.page,
			alias: entry.alias,
			entry,
		});
	};

	// region Plugins
	this._getPlugins = function (pluginType) { return this._plugins[pluginType] ||= []; };

	this._applyPlugins_useFirst = function (pluginType, commonArgs, pluginArgs) {
		for (const plugin of this._getPlugins(pluginType)) {
			const out = plugin(commonArgs, pluginArgs);
			if (out) return out;
		}
	};

	this._applyPlugins_useAll = function (pluginType, commonArgs, pluginArgs) {
		const plugins = this._getPlugins(pluginType);
		if (!plugins?.length) return null;

		let input = pluginArgs.input;
		for (const plugin of plugins) {
			input = plugin(commonArgs, pluginArgs) ?? input;
		}
		return input;
	};

	this._applyPlugins_getAll = function (pluginType, commonArgs, pluginArgs) {
		const plugins = this._getPlugins(pluginType);
		if (!plugins?.length) return [];

		return plugins
			.map(plugin => plugin(commonArgs, pluginArgs))
			.filter(Boolean);
	};
	// endregion

	/**
	 * Recursively walk down a tree of "entry" JSON items, adding to a stack of strings to be finally rendered to the
	 * page. Note that this function does _not_ actually do the rendering, see the example code above for how to display
	 * the result.
	 *
	 * @param entry An "entry" usually defined in JSON. A schema is available in tests/schema
	 * @param textStack A reference to an array, which will hold all our strings as we recurse
	 * @param [meta] Meta state.
	 * @param [meta.depth] The current recursion depth. Optional; default 0, or -1 for type "section" entries.
	 * @param [options] Render options.
	 * @param [options.prefix] String to prefix rendered lines with.
	 * @param [options.suffix] String to suffix rendered lines with.
	 */
	this.recursiveRender = function (entry, textStack, meta, options) {
		if (entry instanceof Array) {
			entry.forEach(nxt => this.recursiveRender(nxt, textStack, meta, options));
			setTimeout(() => { throw new Error(`Array passed to renderer! The renderer only guarantees support for primitives and basic objects.`); });
			return this;
		}

		// respect the API of the original, but set up for using string concatenations
		if (textStack.length === 0) textStack[0] = "";
		else textStack.reverse();

		// initialise meta
		meta = meta || {};
		meta._typeStack = [];
		meta.depth = meta.depth == null ? 0 : meta.depth;

		this._recursiveRender(entry, textStack, meta, options);
		if (this._fnPostProcess) textStack[0] = this._fnPostProcess(textStack[0]);
		textStack.reverse();

		return this;
	};

	/**
	 * Inner rendering code. Uses string concatenation instead of an array stack, for ~2x the speed.
	 * @param entry As above.
	 * @param textStack As above.
	 * @param meta As above, with the addition of...
	 * @param options
	 *          .prefix The (optional) prefix to be added to the textStack before whatever is added by the current call
	 *          .suffix The (optional) suffix to be added to the textStack after whatever is added by the current call
	 * @private
	 */
	this._recursiveRender = function (entry, textStack, meta, options) {
		if (entry == null) return; // Avoid dying on nully entries
		if (!textStack) throw new Error("Missing stack!");
		if (!meta) throw new Error("Missing metadata!");

		options = options || {};

		// For wrapped entries, simply recurse
		if (entry.type === "wrapper") return this._recursiveRender(entry.wrapped, textStack, meta, options);

		if (entry.type === "section") meta.depth = -1;

		meta._didRenderPrefix = false;
		meta._didRenderSuffix = false;

		if (typeof entry === "object") {
			// the root entry (e.g. "Rage" in barbarian "classFeatures") is assumed to be of type "entries"
			const type = entry.type == null || entry.type === "section" ? "entries" : entry.type;

			meta._typeStack.push(type);

			switch (type) {
				// recursive
				case "entries": this._renderEntries(entry, textStack, meta, options); break;
				case "options": this._renderOptions(entry, textStack, meta, options); break;
				case "list": this._renderList(entry, textStack, meta, options); break;

				// inline
				case "inline": this._renderInline(entry, textStack, meta, options); break;
				case "inlineBlock": this._renderInlineBlock(entry, textStack, meta, options); break;
				case "link": this._renderLink(entry, textStack, meta, options); break;

				// homebrew changes
				case "homebrew": this._renderHomebrew(entry, textStack, meta, options); break;

				// misc
				case "code": this._renderCode(entry, textStack, meta, options); break;
				case "hr": this._renderHr(entry, textStack, meta, options); break;
			}

			meta._typeStack.pop();
		} else if (typeof entry === "string") { // block
			this._renderPrefix(entry, textStack, meta, options);
			this._renderString(entry, textStack, meta, options);
			this._renderSuffix(entry, textStack, meta, options);
		} else { // block
			// for ints or any other types which do not require specific rendering
			this._renderPrefix(entry, textStack, meta, options);
			this._renderPrimitive(entry, textStack, meta, options);
			this._renderSuffix(entry, textStack, meta, options);
		}
	};

	this._RE_TEXT_CENTER = /\btext-center\b/g;
	this._RE_COL_D = /\bcol-\d\d?(?:-\d\d?)?\b/g;

	this._getMutatedStyleString = function (str) {
		if (!str) return str;
		return str
			.replace(this._RE_TEXT_CENTER, "ve-$&")
			.replace(this._RE_COL_D, "ve-$&")
		;
	};

	this._renderPrefix = function (entry, textStack, meta, options) {
		if (meta._didRenderPrefix) return;
		if (options.prefix != null) {
			textStack[0] += options.prefix;
			meta._didRenderPrefix = true;
		}
	};

	this._renderSuffix = function (entry, textStack, meta, options) {
		if (meta._didRenderSuffix) return;
		if (options.suffix != null) {
			textStack[0] += options.suffix;
			meta._didRenderSuffix = true;
		}
	};

	this._renderImage_getUrl = function (entry) {
		let url = Renderer.utils.getEntryMediaUrl(entry, "href", "img");
		url = this._applyPlugins_useAll("image_urlPostProcess", null, {input: url}) ?? url;
		return url;
	};

	this._renderImage_getUrlThumbnail = function (entry) {
		let url = Renderer.utils.getEntryMediaUrl(entry, "hrefThumbnail", "img");
		url = this._applyPlugins_useAll("image_urlThumbnailPostProcess", null, {input: url}) ?? url;
		return url;
	};

	this._renderList_getListCssClasses = function (entry, textStack, meta, options) {
		const out = [`rd__list`];
		if (entry.style || entry.columns) {
			if (entry.style) out.push(...entry.style.split(" ").map(it => `rd__${it}`));
			if (entry.columns) out.push(`columns-${entry.columns}`);
		}
		return out.join(" ");
	};

	this._renderEntries = function (entry, textStack, meta, options) {
		this._renderEntriesSubtypes(entry, textStack, meta, options, true);
	};

	this._getPagePart = function (entry, isInset) {
		if (!Renderer.utils.isDisplayPage(entry.page)) return "";
		return ` <span class="rd__title-link ${isInset ? `rd__title-link--inset` : ""}">${entry.source ? `<span class="help-subtle" title="${Parser.sourceJsonToFull(entry.source)}">${Parser.sourceJsonToAbv(entry.source)}</span> ` : ""}p${entry.page}</span>`;
	};

	this._renderEntriesSubtypes = function (entry, textStack, meta, options, incDepth) {
		const type = entry.type || "entries";
		const isInlineTitle = meta.depth >= 2;
		const isAddPeriod = isInlineTitle && entry.name && !Renderer._INLINE_HEADER_TERMINATORS.has(entry.name[entry.name.length - 1]);
		const pagePart = !this._isPartPageExpandCollapseDisabled && !isInlineTitle
			? this._getPagePart(entry)
			: "";
		const partExpandCollapse = !this._isPartPageExpandCollapseDisabled && !isInlineTitle
			? this._getPtExpandCollapse()
			: "";
		const partPageExpandCollapse = !this._isPartPageExpandCollapseDisabled && (pagePart || partExpandCollapse)
			? `<span class="ve-flex-vh-center">${[pagePart, partExpandCollapse].filter(Boolean).join("")}</span>`
			: "";
		const nextDepth = incDepth && meta.depth < 2 ? meta.depth + 1 : meta.depth;
		const styleString = this._renderEntriesSubtypes_getStyleString(entry, meta, isInlineTitle);
		const dataString = this._renderEntriesSubtypes_getDataString(entry);
		if (entry.name != null && Renderer.ENTRIES_WITH_ENUMERATED_TITLES_LOOKUP[entry.type]) this._handleTrackTitles(entry.name);

		const headerTag = isInlineTitle ? "span" : `h${Math.min(Math.max(meta.depth + 2, 1), 6)}`;
		const headerClass = `rd__h--${meta.depth + 1}`; // adjust as the CSS is 0..4 rather than -1..3

		const cachedLastDepthTrackerProps = MiscUtil.copyFast(this._lastDepthTrackerInheritedProps);
		this._handleTrackDepth(entry, meta.depth);

		const pluginDataNamePrefix = this._applyPlugins_getAll(`${type}_namePrefix`, {textStack, meta, options}, {input: entry});

		const headerSpan = entry.name ? `<${headerTag} class="rd__h ${headerClass}" data-title-index="${this._headerIndex++}" ${this._getEnumeratedTitleRel(entry.name)}> <span class="entry-title-inner${!pagePart && entry.source ? ` help-subtle` : ""}"${!pagePart && entry.source ? ` title="Source: ${Parser.sourceJsonToFull(entry.source)}${entry.page ? `, p${entry.page}` : ""}"` : ""}>${pluginDataNamePrefix.join("")}${this.render({type: "inline", entries: [entry.name]})}${isAddPeriod ? "." : ""}</span>${partPageExpandCollapse}</${headerTag}> ` : "";

		if (meta.depth === -1) {
			if (!this._firstSection) textStack[0] += `<hr class="rd__hr rd__hr--section">`;
			this._firstSection = false;
		}

		if (entry.entries || entry.name) {
			textStack[0] += `<${this.wrapperTag} ${dataString} ${styleString}>${headerSpan}`;
			this._renderEntriesSubtypes_renderPreReqText(entry, textStack, meta);
			if (entry.entries) {
				const cacheDepth = meta.depth;
				const len = entry.entries.length;
				for (let i = 0; i < len; ++i) {
					meta.depth = nextDepth;
					this._recursiveRender(entry.entries[i], textStack, meta, {prefix: "<p>", suffix: "</p>"});
					// Add a spacer for style sets that have vertical whitespace instead of indents
					if (i === 0 && cacheDepth >= 2) textStack[0] += `<div class="rd__spc-inline-post"></div>`;
				}
				meta.depth = cacheDepth;
			}
			textStack[0] += `</${this.wrapperTag}>`;
		}

		this._lastDepthTrackerInheritedProps = cachedLastDepthTrackerProps;
	};

	this._renderEntriesSubtypes_getDataString = function (entry) {
		let dataString = "";
		if (entry.source) dataString += `data-source="${entry.source}"`;
		if (entry.data) {
			for (const k in entry.data) {
				if (!k.startsWith("rd-")) continue;
				dataString += ` data-${k}="${`${entry.data[k]}`.escapeQuotes()}"`;
			}
		}
		return dataString;
	};

	this._renderEntriesSubtypes_renderPreReqText = function (entry, textStack, meta) {
		if (entry.prerequisite) {
			textStack[0] += `<span class="rd__prerequisite">Prerequisite: `;
			this._recursiveRender({type: "inline", entries: [entry.prerequisite]}, textStack, meta);
			textStack[0] += `</span>`;
		}
	};

	this._renderEntriesSubtypes_getStyleString = function (entry, meta, isInlineTitle) {
		const styleClasses = ["rd__b"];
		styleClasses.push(this._getStyleClass(entry.type || "entries", entry));
		if (isInlineTitle) {
			if (this._subVariant) styleClasses.push(Renderer.HEAD_2_SUB_VARIANT);
			else styleClasses.push(Renderer.HEAD_2);
		} else styleClasses.push(meta.depth === -1 ? Renderer.HEAD_NEG_1 : meta.depth === 0 ? Renderer.HEAD_0 : Renderer.HEAD_1);
		return styleClasses.length > 0 ? `class="${styleClasses.join(" ")}"` : "";
	};

	this._renderOptions = function (entry, textStack, meta, options) {
		if (!entry.entries) return;
		entry.entries = entry.entries.sort((a, b) => a.name && b.name ? SortUtil.ascSort(a.name, b.name) : a.name ? -1 : b.name ? 1 : 0);

		if (entry.style && entry.style === "list-hang-notitle") {
			const fauxEntry = {
				type: "list",
				style: "list-hang-notitle",
				items: entry.entries.map(ent => {
					if (typeof ent === "string") return ent;
					if (ent.type === "item") return ent;

					const out = {...ent, type: "item"};
					if (ent.name) out.name = Renderer._INLINE_HEADER_TERMINATORS.has(ent.name[ent.name.length - 1]) ? out.name : `${out.name}.`;
					return out;
				}),
			};
			this._renderList(fauxEntry, textStack, meta, options);
		} else this._renderEntriesSubtypes(entry, textStack, meta, options, false);
	};

	this._renderList = function (entry, textStack, meta, options) {
		if (entry.items) {
			const tag = entry.start ? "ol" : "ul";
			const cssClasses = this._renderList_getListCssClasses(entry, textStack, meta, options);
			textStack[0] += `<${tag} ${cssClasses ? `class="${cssClasses}"` : ""} ${entry.start ? `start="${entry.start}"` : ""}>`;
			if (entry.name) textStack[0] += `<li class="rd__list-name">${entry.name}</li>`;
			const isListHang = entry.style && entry.style.split(" ").includes("list-hang");
			const len = entry.items.length;
			for (let i = 0; i < len; ++i) {
				const item = entry.items[i];
				// Special case for child lists -- avoid wrapping in LI tags to avoid double-bullet
				if (item.type !== "list") {
					const className = `${this._getStyleClass(entry.type, item)}${item.type === "itemSpell" ? " rd__li-spell" : ""}`;
					textStack[0] += `<li class="rd__li ${className}">`;
				}
				// If it's a raw string in a hanging list, wrap it in a div to allow for the correct styling
				if (isListHang && typeof item === "string") textStack[0] += "<div>";
				this._recursiveRender(item, textStack, meta);
				if (isListHang && typeof item === "string") textStack[0] += "</div>";
				if (item.type !== "list") textStack[0] += "</li>";
			}
			textStack[0] += `</${tag}>`;
		}
	};

	this._getPtExpandCollapse = function () {
		return `<span class="rd__h-toggle ml-2 clickable no-select" data-rd-h-toggle-button="true" title="Toggle Visibility (CTRL to Toggle All)">[\u2013]</span>`;
	};

	this._renderInline = function (entry, textStack, meta, options) {
		if (entry.entries) {
			const len = entry.entries.length;
			for (let i = 0; i < len; ++i) this._recursiveRender(entry.entries[i], textStack, meta);
		}
	};

	this._renderInlineBlock = function (entry, textStack, meta, options) {
		this._renderPrefix(entry, textStack, meta, options);
		if (entry.entries) {
			const len = entry.entries.length;
			for (let i = 0; i < len; ++i) this._recursiveRender(entry.entries[i], textStack, meta);
		}
		this._renderSuffix(entry, textStack, meta, options);
	};

	this._renderHomebrew = function (entry, textStack, meta, options) {
		textStack[0] += `<div class="rd-homebrew__b"><div class="rd-homebrew__wrp-notice"><span class="rd-homebrew__disp-notice"></span>`;

		if (entry.oldEntries) {
			const hoverMeta = Renderer.hover.getInlineHover({type: "entries", name: "Homebrew", entries: entry.oldEntries});
			let markerText;
			if (entry.movedTo) {
				markerText = "(See moved content)";
			} else if (entry.entries) {
				markerText = "(See replaced content)";
			} else {
				markerText = "(See removed content)";
			}
			textStack[0] += `<span class="rd-homebrew__disp-old-content" href="#${window.location.hash}" ${hoverMeta.html}>${markerText}</span>`;
		}

		textStack[0] += `</div>`;

		if (entry.entries) {
			const len = entry.entries.length;
			for (let i = 0; i < len; ++i) this._recursiveRender(entry.entries[i], textStack, meta, {prefix: "<p>", suffix: "</p>"});
		} else if (entry.movedTo) {
			textStack[0] += `<i>This content has been moved to ${entry.movedTo}.</i>`;
		} else {
			textStack[0] += "<i>This content has been deleted.</i>";
		}

		textStack[0] += `</div>`;
	};

	this._renderCode = function (entry, textStack, meta, options) {
		const isWrapped = !!StorageUtil.syncGet("rendererCodeWrap");
		textStack[0] += `
			<div class="ve-flex-col h-100">
				<div class="ve-flex no-shrink pt-1">
					<button class="btn btn-default btn-xs mb-1 mr-2" onclick="Renderer.events.handleClick_copyCode(event, this)">Copy Code</button>
					<button class="btn btn-default btn-xs mb-1 ${isWrapped ? "active" : ""}" onclick="Renderer.events.handleClick_toggleCodeWrap(event, this)">Word Wrap</button>
				</div>
				<pre class="h-100 w-100 mb-1 ${isWrapped ? "rd__pre-wrap" : ""}">${entry.preformatted}</pre>
			</div>
		`;
	};

	this._renderHr = function (entry, textStack, meta, options) {
		textStack[0] += `<hr class="rd__hr">`;
	};

	this._getStyleClass = function (entryType, entry) {
		const outList = [];

		const pluginResults = this._applyPlugins_getAll(`${entryType}_styleClass_fromSource`, null, {input: {entryType, entry}});

		if (!pluginResults.some(it => it.isSkip)) {
			if (
				SourceUtil.isNonstandardSource(entry.source)
				|| (typeof PrereleaseUtil !== "undefined" && PrereleaseUtil.hasSourceJson(entry.source))
			) outList.push("spicy-sauce");
			if (typeof BrewUtil2 !== "undefined" && BrewUtil2.hasSourceJson(entry.source)) outList.push("refreshing-brew");
		}

		if (this._extraSourceClasses) outList.push(...this._extraSourceClasses);
		for (const k in this._fnsGetStyleClasses) {
			const fromFn = this._fnsGetStyleClasses[k](entry);
			if (fromFn) outList.push(...fromFn);
		}
		if (entry.style) outList.push(this._getMutatedStyleString(entry.style));
		return outList.join(" ");
	};

	this._renderString = function (entry, textStack, meta, options) {
		const str = this._applyPlugins_useAll("string_preprocess", {textStack, meta, options}, {input: entry}) ?? entry;

		const tagSplit = Renderer.splitByTags(str);
		const len = tagSplit.length;
		for (let i = 0; i < len; ++i) {
			const s = tagSplit[i];
			if (!s) continue;

			if (!s.startsWith("{@")) {
				this._renderString_renderBasic(textStack, meta, options, s);
				continue;
			}

			const [tag, text] = Renderer.splitFirstSpace(s.slice(1, -1));
			this._renderString_renderTag(textStack, meta, options, tag, text);
		}
	};

	this._renderString_renderBasic = function (textStack, meta, options, str) {
		const fromPlugins = this._applyPlugins_useFirst("string_basic", {textStack, meta, options}, {input: str});
		if (fromPlugins) return void (textStack[0] += fromPlugins);

		textStack[0] += str;
	};

	this._renderString_renderTag = function (textStack, meta, options, tag, text) {
		// region Plugins
		// Tag-specific
		const fromPluginsSpecific = this._applyPlugins_useFirst(`string_${tag}`, {textStack, meta, options}, {input: {tag, text}});
		if (fromPluginsSpecific) return void (textStack[0] += fromPluginsSpecific);

		// Generic
		const fromPluginsGeneric = this._applyPlugins_useFirst("string_tag", {textStack, meta, options}, {input: {tag, text}});
		if (fromPluginsGeneric) return void (textStack[0] += fromPluginsGeneric);
		// endregion

		switch (tag) {
			// BASIC STYLES/TEXT ///////////////////////////////////////////////////////////////////////////////
			case "@b":
			case "@bold":
				textStack[0] += `<b>`;
				this._recursiveRender(text, textStack, meta);
				textStack[0] += `</b>`;
				break;
			case "@i":
			case "@italic":
				textStack[0] += `<i>`;
				this._recursiveRender(text, textStack, meta);
				textStack[0] += `</i>`;
				break;
			case "@s":
			case "@strike":
				textStack[0] += `<s>`;
				this._recursiveRender(text, textStack, meta);
				textStack[0] += `</s>`;
				break;
			case "@s2":
			case "@strikeDouble":
				textStack[0] += `<s class="ve-strike-double">`;
				this._recursiveRender(text, textStack, meta);
				textStack[0] += `</s>`;
				break;
			case "@u":
			case "@underline":
				textStack[0] += `<u>`;
				this._recursiveRender(text, textStack, meta);
				textStack[0] += `</u>`;
				break;
			case "@u2":
			case "@underlineDouble":
				textStack[0] += `<u class="ve-underline-double">`;
				this._recursiveRender(text, textStack, meta);
				textStack[0] += `</u>`;
				break;
			case "@sup":
				textStack[0] += `<sup>`;
				this._recursiveRender(text, textStack, meta);
				textStack[0] += `</sup>`;
				break;
			case "@sub":
				textStack[0] += `<sub>`;
				this._recursiveRender(text, textStack, meta);
				textStack[0] += `</sub>`;
				break;
			case "@kbd":
				textStack[0] += `<kbd>`;
				this._recursiveRender(text, textStack, meta);
				textStack[0] += `</kbd>`;
				break;
			case "@code":
				textStack[0] += `<span class="code">`;
				this._recursiveRender(text, textStack, meta);
				textStack[0] += `</span>`;
				break;
			case "@style": {
				const [displayText, styles] = Renderer.splitTagByPipe(text);
				const classNames = (styles || "").split(";").map(it => Renderer._STYLE_TAG_ID_TO_STYLE[it.trim()]).filter(Boolean).join(" ");
				textStack[0] += `<span class="${classNames}">`;
				this._recursiveRender(displayText, textStack, meta);
				textStack[0] += `</span>`;
				break;
			}
			case "@font": {
				const [displayText, fontFamily] = Renderer.splitTagByPipe(text);
				textStack[0] += `<span style="font-family: '${fontFamily}'">`;
				this._recursiveRender(displayText, textStack, meta);
				textStack[0] += `</span>`;
				break;
			}
			case "@note":
				textStack[0] += `<i class="ve-muted">`;
				this._recursiveRender(text, textStack, meta);
				textStack[0] += `</i>`;
				break;
			case "@tip": {
				const [displayText, titielText] = Renderer.splitTagByPipe(text);
				textStack[0] += `<span title="${titielText.qq()}">`;
				this._recursiveRender(displayText, textStack, meta);
				textStack[0] += `</span>`;
				break;
			}
			case "@atk":
				textStack[0] += `<i>${Renderer.attackTagToFull(text)}</i>`;
				break;
			case "@h": textStack[0] += `<i>Hit:</i> `; break;
			case "@m": textStack[0] += `<i>Miss:</i> `; break;
			case "@color": {
				const [toDisplay, color] = Renderer.splitTagByPipe(text);
				const ptColor = this._renderString_renderTag_getBrewColorPart(color);

				textStack[0] += `<span class="rd__color" style="color: ${ptColor}">`;
				this._recursiveRender(toDisplay, textStack, meta);
				textStack[0] += `</span>`;
				break;
			}
			case "@highlight": {
				const [toDisplay, color] = Renderer.splitTagByPipe(text);
				const ptColor = this._renderString_renderTag_getBrewColorPart(color);

				textStack[0] += ptColor ? `<span style="background-color: ${ptColor}">` : `<span class="rd__highlight">`;
				textStack[0] += toDisplay;
				textStack[0] += `</span>`;
				break;
			}
			case "@help": {
				const [toDisplay, title = ""] = Renderer.splitTagByPipe(text);
				textStack[0] += `<span class="help" title="${title.qq()}">`;
				this._recursiveRender(toDisplay, textStack, meta);
				textStack[0] += `</span>`;
				break;
			}

			// Comic styles ////////////////////////////////////////////////////////////////////////////////////
			case "@comic":
				textStack[0] += `<span class="rd__comic">`;
				this._recursiveRender(text, textStack, meta);
				textStack[0] += `</span>`;
				break;
			case "@comicH1":
				textStack[0] += `<span class="rd__comic rd__comic--h1">`;
				this._recursiveRender(text, textStack, meta);
				textStack[0] += `</span>`;
				break;
			case "@comicH2":
				textStack[0] += `<span class="rd__comic rd__comic--h2">`;
				this._recursiveRender(text, textStack, meta);
				textStack[0] += `</span>`;
				break;
			case "@comicH3":
				textStack[0] += `<span class="rd__comic rd__comic--h3">`;
				this._recursiveRender(text, textStack, meta);
				textStack[0] += `</span>`;
				break;
			case "@comicH4":
				textStack[0] += `<span class="rd__comic rd__comic--h4">`;
				this._recursiveRender(text, textStack, meta);
				textStack[0] += `</span>`;
				break;
			case "@comicNote":
				textStack[0] += `<span class="rd__comic rd__comic--note">`;
				this._recursiveRender(text, textStack, meta);
				textStack[0] += `</span>`;
				break;

			// DICE ////////////////////////////////////////////////////////////////////////////////////////////
			case "@dice":
			case "@autodice": {
				const fauxEntry = Renderer.utils.getTagEntry(tag, text);
				this._recursiveRender(fauxEntry, textStack, meta);

				break;
			}

			// LINKS ///////////////////////////////////////////////////////////////////////////////////////////
			case "@filter": {
				// format: {@filter Warlock Spells|spells|level=1;2|class=Warlock}
				const [displayText, page, ...filters] = Renderer.splitTagByPipe(text);

				const filterSubhashMeta = Renderer.getFilterSubhashes(filters);

				const fauxEntry = {
					type: "link",
					text: displayText,
					href: {
						type: "internal",
						path: `${page}.html`,
						hash: HASH_BLANK,
						hashPreEncoded: true,
						subhashes: filterSubhashMeta.subhashes,
					},
				};

				if (filterSubhashMeta.customHash) fauxEntry.href.hash = filterSubhashMeta.customHash;

				this._recursiveRender(fauxEntry, textStack, meta);

				break;
			}
			case "@link": {
				const [displayText, url] = Renderer.splitTagByPipe(text);
				let outUrl = url == null ? displayText : url;

				// If a URL is prefixed with e.g. `https://` or `mailto:`, leave it as-is
				// Otherwise, assume `http` (avoid HTTPS, as the D&D homepage doesn't support it)
				if (!/^[a-zA-Z]+:/.test(outUrl)) outUrl = `http://${outUrl}`;

				const fauxEntry = {
					type: "link",
					href: {
						type: "external",
						url: outUrl,
					},
					text: displayText,
				};
				this._recursiveRender(fauxEntry, textStack, meta);

				break;
			}

			// OTHER HOVERABLES ////////////////////////////////////////////////////////////////////////////////
			case "@footnote": {
				const [displayText, footnoteText, optTitle] = Renderer.splitTagByPipe(text);
				const hoverMeta = Renderer.hover.getInlineHover({
					type: "entries",
					name: optTitle ? optTitle.toTitleCase() : "Footnote",
					entries: [footnoteText, optTitle ? `{@note ${optTitle}}` : ""].filter(Boolean),
				});
				textStack[0] += `<span class="help" ${hoverMeta.html}>`;
				this._recursiveRender(displayText, textStack, meta);
				textStack[0] += `</span>`;

				break;
			}
			case "@homebrew": {
				const [newText, oldText] = Renderer.splitTagByPipe(text);
				const tooltipEntries = [];
				if (newText && oldText) {
					tooltipEntries.push("{@b This is a homebrew addition, replacing the following:}");
				} else if (newText) {
					tooltipEntries.push("{@b This is a homebrew addition.}");
				} else if (oldText) {
					tooltipEntries.push("{@b The following text has been removed with this homebrew:}");
				}
				if (oldText) {
					tooltipEntries.push(oldText);
				}
				const hoverMeta = Renderer.hover.getInlineHover({
					type: "entries",
					name: "Homebrew Modifications",
					entries: tooltipEntries,
				});
				textStack[0] += `<span class="rd-homebrew__disp-inline" ${hoverMeta.html}>`;
				this._recursiveRender(newText || "[...]", textStack, meta);
				textStack[0] += `</span>`;

				break;
			}

			// HOMEBREW LOADING ////////////////////////////////////////////////////////////////////////////////
			case "@loader": {
				const {name, path, mode} = this._renderString_getLoaderTagMeta(text);

				const brewUtilName = mode === "homebrew" ? "BrewUtil2" : mode === "prerelease" ? "PrereleaseUtil" : null;
				const brewUtil = globalThis[brewUtilName];

				if (!brewUtil) {
					textStack[0] += `<span class="text-danger" title="Unknown loader mode &quot;${mode.qq()}&quot;!">${name}<span class="glyphicon glyphicon-alert rd__loadbrew-icon rd__loadbrew-icon"></span></span>`;

					break;
				}

				textStack[0] += `<span onclick="${brewUtilName}.pAddBrewFromLoaderTag(this)" data-rd-loader-path="${path.escapeQuotes()}" data-rd-loader-name="${name.escapeQuotes()}" class="rd__wrp-loadbrew--ready" title="Click to install ${brewUtil.DISPLAY_NAME}">${name}<span class="glyphicon glyphicon-download-alt rd__loadbrew-icon rd__loadbrew-icon"></span></span>`;
				break;
			}

			default: {
				const {name, source, displayText, others, page, hash, hashPreEncoded, pageHover, hashHover, hashPreEncodedHover, preloadId, linkText, subhashes, subhashesHover, isFauxPage} = Renderer.utils.getTagMeta(tag, text);

				const fauxEntry = {
					type: "link",
					href: {
						type: "internal",
						path: page,
						hash,
						hover: {
							page,
							isFauxPage,
							source,
						},
					},
					text: (displayText || name),
				};

				if (hashPreEncoded != null) fauxEntry.href.hashPreEncoded = hashPreEncoded;
				if (pageHover != null) fauxEntry.href.hover.page = pageHover;
				if (hashHover != null) fauxEntry.href.hover.hash = hashHover;
				if (hashPreEncodedHover != null) fauxEntry.href.hover.hashPreEncoded = hashPreEncodedHover;
				if (preloadId != null) fauxEntry.href.hover.preloadId = preloadId;
				if (linkText) fauxEntry.text = linkText;
				if (subhashes) fauxEntry.href.subhashes = subhashes;
				if (subhashesHover) fauxEntry.href.hover.subhashes = subhashesHover;

				this._recursiveRender(fauxEntry, textStack, meta);

				break;
			}
		}
	};

	this._renderString_renderTag_getBrewColorPart = function (color) {
		if (!color) return "";
		const scrubbedColor = BrewUtilShared.getValidColor(color, {isExtended: true});
		return scrubbedColor.startsWith("--") ? `var(${scrubbedColor})` : `#${scrubbedColor}`;
	};

	this._renderString_getLoaderTagMeta = function (text, {isDefaultUrl = false} = {}) {
		const [name, file, mode = "homebrew"] = Renderer.splitTagByPipe(text);

		if (!isDefaultUrl) return {name, path: file, mode};

		const path = /^.*?:\/\//.test(file) ? file : `${VeCt.URL_ROOT_BREW}${file}`;
		return {name, path, mode};
	};

	this._renderPrimitive = function (entry, textStack, meta, options) { textStack[0] += entry; };

	this._renderLink = function (entry, textStack, meta, options) {
		let href = this._renderLink_getHref(entry);

		const pluginData = this._applyPlugins_getAll("link", {textStack, meta, options}, {input: entry});
		const isDisableEvents = pluginData.some(it => it.isDisableEvents);
		const additionalAttributes = pluginData.map(it => it.attributes).filter(Boolean);

		if (this._isInternalLinksDisabled && entry.href.type === "internal") {
			textStack[0] += `<span class="bold" ${isDisableEvents ? "" : this._renderLink_getHoverString(entry)} ${additionalAttributes.join(" ")}>${this.render(entry.text)}</span>`;
		} else if (entry.href.hover?.isFauxPage) {
			textStack[0] += `<span class="help help--hover" ${isDisableEvents ? "" : this._renderLink_getHoverString(entry)} ${additionalAttributes.join(" ")}>${this.render(entry.text)}</span>`;
		} else {
			textStack[0] += `<a href="${href.qq()}" ${entry.href.type === "internal" ? "" : `target="_blank" rel="noopener noreferrer"`} ${isDisableEvents ? "" : this._renderLink_getHoverString(entry)} ${additionalAttributes.join(" ")}>${this.render(entry.text)}</a>`;
		}
	};

	this._renderLink_getHref = function (entry) {
		if (entry.href.type === "internal") {
			// baseURL is blank by default
			const ptBase = `${this.baseUrl}${entry.href.path}`;
			let ptHash = "";
			if (entry.href.hash != null) {
				ptHash += entry.href.hashPreEncoded ? entry.href.hash : UrlUtil.encodeForHash(entry.href.hash);
			}
			if (entry.href.subhashes != null) {
				ptHash += Renderer.utils.getLinkSubhashString(entry.href.subhashes);
			}
			if (!ptHash) return ptBase;
			return `${ptBase}#${ptHash}`;
		}
		if (entry.href.type === "external") {
			return entry.href.url;
		}
		return "";
	};

	this._renderLink_getHoverString = function (entry) {
		if (!entry.href.hover || !this._isAddHandlers) return "";

		let procHash = entry.href.hover.hash
			? entry.href.hover.hashPreEncoded ? entry.href.hover.hash : UrlUtil.encodeForHash(entry.href.hover.hash)
			: entry.href.hashPreEncoded ? entry.href.hash : UrlUtil.encodeForHash(entry.href.hash);

		if (this._tagExportDict) {
			this._tagExportDict[procHash] = {
				page: entry.href.hover.page,
				source: entry.href.hover.source,
				hash: procHash,
			};
		}

		if (entry.href.hover.subhashes) {
			procHash += Renderer.utils.getLinkSubhashString(entry.href.hover.subhashes);
		}

		const pluginData = this._applyPlugins_getAll("link_attributesHover", null, {input: {entry, procHash}});
		const replacementAttributes = pluginData.map(it => it.attributesHoverReplace).filter(Boolean);
		if (replacementAttributes.length) return replacementAttributes.join(" ");

		return [
			`onmouseover="Renderer.hover.pHandleLinkMouseOver(event, this)"`,
			`onmouseleave="Renderer.hover.handleLinkMouseLeave(event, this)"`,
			`onmousemove="Renderer.hover.handleLinkMouseMove(event, this)"`,
			`onclick="Renderer.hover.handleLinkClick(event, this)"`,
			`ondragstart="Renderer.hover.handleLinkDragStart(event, this)"`,
			`data-vet-page="${entry.href.hover.page.qq()}"`,
			`data-vet-source="${entry.href.hover.source.qq()}"`,
			`data-vet-hash="${procHash.qq()}"`,
			entry.href.hover.preloadId != null ? `data-vet-preload-id="${`${entry.href.hover.preloadId}`.qq()}"` : "",
			entry.href.hover.isFauxPage ? `data-vet-is-faux-page="true"` : "",
			Renderer.hover.getPreventTouchString(),
		]
			.filter(Boolean)
			.join(" ");
	};

	/**
	 * Helper function to render an entity using this renderer
	 * @param entry
	 * @param depth
	 * @returns {string}
	 */
	this.render = function (entry, depth = 0) {
		const tempStack = [];
		this.recursiveRender(entry, tempStack, {depth});
		return tempStack.join("");
	};
};

// Unless otherwise specified, these use `"name"` as their name title prop
Renderer.ENTRIES_WITH_ENUMERATED_TITLES = [
	{type: "section", key: "entries", depth: -1},
	{type: "entries", key: "entries", depthIncrement: 1},
	{type: "options", key: "entries"},
	{type: "inset", key: "entries", depth: 2},
	{type: "insetReadaloud", key: "entries", depth: 2},
	{type: "variant", key: "entries", depth: 2},
	{type: "variantInner", key: "entries", depth: 2},
	{type: "actions", key: "entries", depth: 2},
	{type: "flowBlock", key: "entries", depth: 2},
	{type: "optfeature", key: "entries", depthIncrement: 1},
	{type: "patron", key: "entries"},
];

Renderer.ENTRIES_WITH_ENUMERATED_TITLES_LOOKUP = Renderer.ENTRIES_WITH_ENUMERATED_TITLES.mergeMap(it => ({[it.type]: it}));

Renderer.ENTRIES_WITH_CHILDREN = [
	...Renderer.ENTRIES_WITH_ENUMERATED_TITLES,
	{type: "list", key: "items"},
	{type: "table", key: "rows"},
];

Renderer._INLINE_HEADER_TERMINATORS = new Set([".", ",", "!", "?", ";", ":", `"`]);

Renderer._STYLE_TAG_ID_TO_STYLE = {
	"small-caps": "small-caps",
	"small": "ve-small",
	"large": "ve-large",
	"capitalize": "capitalize",
	"dnd-font": "dnd-font",
};

Renderer.get = () => {
	if (!Renderer.defaultRenderer) Renderer.defaultRenderer = new Renderer();
	return Renderer.defaultRenderer;
};

/**
 * Note that a tag (`{@tag ...}`) is not valid inside a property injector (`{=prop ...}`),
 *   but a property injector *is* valid inside a tag.
 */
Renderer.applyProperties = function (entry, object) {
	const propSplit = Renderer.splitByTags(entry);
	const len = propSplit.length;
	if (len === 1) return entry;

	let textStack = "";

	for (let i = 0; i < len; ++i) {
		const s = propSplit[i];
		if (!s) continue;

		if (s.startsWith("{@")) {
			const [tag, text] = Renderer.splitFirstSpace(s.slice(1, -1));
			textStack += `{${tag} ${Renderer.applyProperties(text, object)}}`;
			continue;
		}

		if (!s.startsWith("{=")) {
			textStack += s;
			continue;
		}

		if (s.startsWith("{=")) {
			const [path, modifiers] = s.slice(2, -1).split("/");
			let fromProp = object[path];

			if (!modifiers) {
				textStack += fromProp;
				continue;
			}

			if (fromProp == null) throw new Error(`Could not apply property in "${s}"; "${path}" value was null!`);

			modifiers
				.split("")
				.sort((a, b) => Renderer.applyProperties._OP_ORDER.indexOf(a) - Renderer.applyProperties._OP_ORDER.indexOf(b));

			for (const modifier of modifiers) {
				switch (modifier) {
					case "a": // render "a"/"an" depending on prop value
						fromProp = Renderer.applyProperties._LEADING_AN.has(fromProp[0].toLowerCase()) ? "an" : "a";
						break;

					case "l": fromProp = fromProp.toLowerCase(); break; // convert text to lower case
					case "t": fromProp = fromProp.toTitleCase(); break; // title-case text
					case "u": fromProp = fromProp.toUpperCase(); break; // uppercase text
					case "v": fromProp = Parser.numberToVulgar(fromProp); break; // vulgarize number
					case "x": fromProp = Parser.numberToText(fromProp); break; // convert number to text
					case "r": fromProp = Math.round(fromProp); break; // round number
					case "f": fromProp = Math.floor(fromProp); break; // floor number
					case "c": fromProp = Math.ceil(fromProp); break; // ceiling number

					default: throw new Error(`Unhandled property modifier "${modifier}"`);
				}
			}

			textStack += fromProp;
		}
	}

	return textStack;
};
Renderer.applyProperties._LEADING_AN = new Set(["a", "e", "i", "o", "u"]);
Renderer.applyProperties._OP_ORDER = [
	"r", "f", "c", // operate on value first
	"v", "x", // cast to desired type
	"l", "t", "u", "a", // operate on value representation
];

Renderer.applyAllProperties = function (entries, object = null) {
	let lastObj = null;
	const handlers = {
		object: (obj) => {
			lastObj = obj;
			return obj;
		},
		string: (str) => Renderer.applyProperties(str, object || lastObj),
	};
	return MiscUtil.getWalker().walk(entries, handlers);
};

Renderer.attackTagToFull = function (tagStr) {
	function renderTag (tags) {
		return `${tags.includes("m") ? "Melee " : tags.includes("r") ? "Ranged " : tags.includes("g") ? "Magical " : tags.includes("a") ? "Area " : ""}${tags.includes("w") ? "Weapon " : tags.includes("s") ? "Spell " : tags.includes("p") ? "Power " : ""}`;
	}

	const tagGroups = tagStr.toLowerCase().split(",").map(it => it.trim()).filter(it => it).map(it => it.split(""));
	if (tagGroups.length > 1) {
		const seen = new Set(tagGroups.last());
		for (let i = tagGroups.length - 2; i >= 0; --i) {
			tagGroups[i] = tagGroups[i].filter(it => {
				const out = !seen.has(it);
				seen.add(it);
				return out;
			});
		}
	}
	return `${tagGroups.map(it => renderTag(it)).join(" or ")}Attack:`;
};

Renderer.splitFirstSpace = function (string) {
	const firstIndex = string.indexOf(" ");
	return firstIndex === -1 ? [string, ""] : [string.substr(0, firstIndex), string.substr(firstIndex + 1)];
};

Renderer._SPLIT_BY_TAG_LEADING_CHARS = new Set(["@", "="]);

Renderer.splitByTags = function (string) {
	let tagDepth = 0;
	let char, char2;
	const out = [];
	let curStr = "";
	let isPrevCharOpenBrace = false;

	const pushOutput = () => {
		if (!curStr) return;
		out.push(curStr);
	};

	const len = string.length;
	for (let i = 0; i < len; ++i) {
		char = string[i];
		char2 = string[i + 1];

		switch (char) {
			case "{":
				if (!Renderer._SPLIT_BY_TAG_LEADING_CHARS.has(char2)) {
					isPrevCharOpenBrace = false;
					curStr += "{";
					break;
				}

				isPrevCharOpenBrace = true;

				if (tagDepth++ > 0) {
					curStr += "{";
				} else {
					pushOutput();
					curStr = `{${char2}`;
					++i;
				}

				break;

			case "}":
				isPrevCharOpenBrace = false;
				curStr += "}";
				if (tagDepth !== 0 && --tagDepth === 0) {
					pushOutput();
					curStr = "";
				}
				break;

			case "@":
			case "=": {
				curStr += char;
				break;
			}

			default: isPrevCharOpenBrace = false; curStr += char; break;
		}
	}

	pushOutput();

	return out;
};

Renderer._splitByPipeBase = function (leadingCharacter) {
	return function (string) {
		let tagDepth = 0;
		let char, char2;
		const out = [];
		let curStr = "";

		const len = string.length;
		for (let i = 0; i < len; ++i) {
			char = string[i];
			char2 = string[i + 1];

			switch (char) {
				case "{":
					if (char2 === leadingCharacter) tagDepth++;
					curStr += "{";

					break;

				case "}":
					if (tagDepth) tagDepth--;
					curStr += "}";

					break;

				case "|": {
					if (tagDepth) curStr += "|";
					else {
						out.push(curStr);
						curStr = "";
					}
					break;
				}

				default: {
					curStr += char;
					break;
				}
			}
		}

		if (curStr) out.push(curStr);
		return out;
	};
};

Renderer.splitTagByPipe = Renderer._splitByPipeBase("@");

Renderer.getEntryDice = function (entry, name, opts = {}) {
	const toDisplay = Renderer.getEntryDiceDisplayText(entry);

	if (entry.rollable === true) return Renderer.getRollableEntryDice(entry, name, toDisplay, opts);
	else return toDisplay;
};

Renderer.getRollableEntryDice = function (
	entry,
	name,
	toDisplay,
	{
		isAddHandlers = true,
		pluginResults = null,
	} = {},
) {
	const toPack = MiscUtil.copyFast(entry);
	if (typeof toPack.toRoll !== "string") {
		// handle legacy format
		toPack.toRoll = Renderer.legacyDiceToString(toPack.toRoll);
	}

	const handlerPart = isAddHandlers ? `onmousedown="event.preventDefault()" data-packed-dice='${JSON.stringify(toPack).qq()}'` : "";

	const rollableTitlePart = isAddHandlers ? Renderer.getEntryDiceTitle(toPack.subType) : null;
	const titlePart = isAddHandlers
		? `title="${[name, rollableTitlePart].filter(Boolean).join(". ").qq()}" ${name ? `data-roll-name="${name}"` : ""}`
		: name ? `title="${name.qq()}" data-roll-name="${name.qq()}"` : "";

	const additionalDataPart = (pluginResults || [])
		.filter(it => it.additionalData)
		.map(it => {
			return Object.entries(it.additionalData)
				.map(([dataKey, val]) => `${dataKey}='${typeof val === "object" ? JSON.stringify(val).qq() : `${val}`.qq()}'`)
				.join(" ");
		})
		.join(" ");

	toDisplay = (pluginResults || []).filter(it => it.toDisplay)[0]?.toDisplay ?? toDisplay;

	const ptRoll = Renderer.getRollableEntryDice._getPtRoll(toPack);

	return `<span class="roller render-roller" ${titlePart} ${handlerPart} ${additionalDataPart}>${toDisplay}</span>${ptRoll}`;
};

Renderer.getRollableEntryDice._getPtRoll = (toPack) => {
	if (!toPack.autoRoll) return "";

	const r = Renderer.dice.parseRandomise2(toPack.toRoll);
	return ` (<span data-rd-is-autodice-result="true">${r}</span>)`;
};

Renderer.getEntryDiceTitle = function (subType) {
	return `Click to roll. ${subType === "damage" ? "SHIFT to roll a critical hit, CTRL to half damage (rounding down)." : subType === "d20" ? "SHIFT to roll with advantage, CTRL to roll with disadvantage." : "SHIFT/CTRL to roll twice."}`;
};

Renderer.legacyDiceToString = function (array) {
	let stack = "";
	array.forEach(r => {
		stack += `${r.neg ? "-" : stack === "" ? "" : "+"}${r.number || 1}d${r.faces}${r.mod ? r.mod > 0 ? `+${r.mod}` : r.mod : ""}`;
	});
	return stack;
};

Renderer.getEntryDiceDisplayText = function (entry) {
	if (entry.displayText) return entry.displayText;
	return Renderer._getEntryDiceDisplayText_getDiceAsStr(entry);
};

Renderer._getEntryDiceDisplayText_getDiceAsStr = function (entry) {
	if (entry.successThresh != null) return `${entry.successThresh} percent`;
	if (typeof entry.toRoll === "string") return entry.toRoll;
	// handle legacy format
	return Renderer.legacyDiceToString(entry.toRoll);
};

Renderer.parseScaleDice = function (tag, text) {
	// format: {@scaledice 2d6;3d6|2-8,9|1d6|psi|display text} (or @scaledamage)
	const [baseRoll, progression, addPerProgress, renderMode, displayText] = Renderer.splitTagByPipe(text);
	const progressionParse = MiscUtil.parseNumberRange(progression, 1, 9);
	const baseLevel = Math.min(...progressionParse);
	const options = {};
	const isMultableDice = /^(\d+)d(\d+)$/i.exec(addPerProgress);

	const getSpacing = () => {
		let diff = null;
		const sorted = [...progressionParse].sort(SortUtil.ascSort);
		for (let i = 1; i < sorted.length; ++i) {
			const prev = sorted[i - 1];
			const curr = sorted[i];
			if (diff == null) diff = curr - prev;
			else if (curr - prev !== diff) return null;
		}
		return diff;
	};

	const spacing = getSpacing();
	progressionParse.forEach(k => {
		const offset = k - baseLevel;
		if (isMultableDice && spacing != null) {
			options[k] = offset ? `${Number(isMultableDice[1]) * (offset / spacing)}d${isMultableDice[2]}` : "";
		} else {
			options[k] = offset ? [...new Array(Math.floor(offset / spacing))].map(_ => addPerProgress).join("+") : "";
		}
	});

	const out = {
		type: "dice",
		rollable: true,
		toRoll: baseRoll,
		displayText: displayText || addPerProgress,
		prompt: {
			entry: renderMode === "psi" ? "Spend Psi Points..." : "Cast at...",
			mode: renderMode,
			options,
		},
	};
	if (tag === "@scaledamage") out.subType = "damage";

	return out;
};

Renderer.getAbilityData = function (abArr, {isOnlyShort, isCurrentLineage} = {}) {
	if (isOnlyShort && isCurrentLineage) return new Renderer._AbilityData({asTextShort: "Lineage (choose)"});

	const outerStack = (abArr || [null]).map(it => Renderer.getAbilityData._doRenderOuter(it));
	if (outerStack.length <= 1) return outerStack[0];
	return new Renderer._AbilityData({
		asText: `Choose one of: ${outerStack.map((it, i) => `(${Parser.ALPHABET[i].toLowerCase()}) ${it.asText}`).join(" ")}`,
		asTextShort: `${outerStack.map((it, i) => `(${Parser.ALPHABET[i].toLowerCase()}) ${it.asTextShort}`).join(" ")}`,
		asCollection: [...new Set(outerStack.map(it => it.asCollection).flat())],
		areNegative: [...new Set(outerStack.map(it => it.areNegative).flat())],
	});
};

Renderer.getAbilityData._doRenderOuter = function (abObj) {
	const mainAbs = [];
	const asCollection = [];
	const areNegative = [];
	const toConvertToText = [];
	const toConvertToShortText = [];

	if (abObj != null) {
		handleAllAbilities(abObj);
		handleAbilitiesChoose();
		return new Renderer._AbilityData({
			asText: toConvertToText.join("; "),
			asTextShort: toConvertToShortText.join("; "),
			asCollection: asCollection,
			areNegative: areNegative,
		});
	}

	return new Renderer._AbilityData();

	function handleAllAbilities (abObj, targetList) {
		MiscUtil.copyFast(Parser.ABIL_ABVS)
			.sort((a, b) => SortUtil.ascSort(abObj[b] || 0, abObj[a] || 0))
			.forEach(shortLabel => handleAbility(abObj, shortLabel, targetList));
	}

	function handleAbility (abObj, shortLabel, optToConvertToTextStorage) {
		if (abObj[shortLabel] != null) {
			const isNegMod = abObj[shortLabel] < 0;
			const toAdd = `${shortLabel.uppercaseFirst()} ${(isNegMod ? "" : "+")}${abObj[shortLabel]}`;

			if (optToConvertToTextStorage) {
				optToConvertToTextStorage.push(toAdd);
			} else {
				toConvertToText.push(toAdd);
				toConvertToShortText.push(toAdd);
			}

			mainAbs.push(shortLabel.uppercaseFirst());
			asCollection.push(shortLabel);
			if (isNegMod) areNegative.push(shortLabel);
		}
	}

	function handleAbilitiesChoose () {
		if (abObj.choose != null) {
			const ch = abObj.choose;
			let outStack = "";
			if (ch.weighted) {
				const w = ch.weighted;
				const froms = w.from.map(it => it.uppercaseFirst());
				const isAny = froms.length === 6;
				const isAllEqual = w.weights.unique().length === 1;
				let cntProcessed = 0;

				const weightsIncrease = w.weights.filter(it => it >= 0).sort(SortUtil.ascSort).reverse();
				const weightsReduce = w.weights.filter(it => it < 0).map(it => -it).sort(SortUtil.ascSort);

				const areIncreaseShort = [];
				const areIncrease = isAny && isAllEqual && w.weights.length > 1 && w.weights[0] >= 0
					? (() => {
						weightsIncrease.forEach(it => areIncreaseShort.push(`+${it}`));
						return [`${cntProcessed ? "choose " : ""}${Parser.numberToText(w.weights.length)} different +${weightsIncrease[0]}`];
					})()
					: weightsIncrease.map(it => {
						areIncreaseShort.push(`+${it}`);
						if (isAny) return `${cntProcessed ? "choose " : ""}any ${cntProcessed++ ? `other ` : ""}+${it}`;
						return `one ${cntProcessed++ ? `other ` : ""}ability to increase by ${it}`;
					});

				const areReduceShort = [];
				const areReduce = isAny && isAllEqual && w.weights.length > 1 && w.weights[0] < 0
					? (() => {
						weightsReduce.forEach(it => areReduceShort.push(`-${it}`));
						return [`${cntProcessed ? "choose " : ""}${Parser.numberToText(w.weights.length)} different -${weightsReduce[0]}`];
					})()
					: weightsReduce.map(it => {
						areReduceShort.push(`-${it}`);
						if (isAny) return `${cntProcessed ? "choose " : ""}any ${cntProcessed++ ? `other ` : ""}-${it}`;
						return `one ${cntProcessed++ ? `other ` : ""}ability to decrease by ${it}`;
					});

				const startText = isAny
					? `Choose `
					: `From ${froms.joinConjunct(", ", " and ")} choose `;

				const ptAreaIncrease = isAny
					? areIncrease.concat(areReduce).join("; ")
					: areIncrease.concat(areReduce).joinConjunct(", ", isAny ? "; " : " and ");
				toConvertToText.push(`${startText}${ptAreaIncrease}`);
				toConvertToShortText.push(`${isAny ? "Any combination " : ""}${areIncreaseShort.concat(areReduceShort).join("/")}${isAny ? "" : ` from ${froms.join("/")}`}`);
			} else {
				const allAbilities = ch.from.length === 6;
				const allAbilitiesWithParent = isAllAbilitiesWithParent(ch);
				let amount = ch.amount === undefined ? 1 : ch.amount;
				amount = (amount < 0 ? "" : "+") + amount;
				if (allAbilities) {
					outStack += "any ";
				} else if (allAbilitiesWithParent) {
					outStack += "any other ";
				}
				if (ch.count != null && ch.count > 1) {
					outStack += `${Parser.numberToText(ch.count)} `;
				}
				if (allAbilities || allAbilitiesWithParent) {
					outStack += `${ch.count > 1 ? "unique " : ""}${amount}`;
				} else {
					for (let j = 0; j < ch.from.length; ++j) {
						let suffix = "";
						if (ch.from.length > 1) {
							if (j === ch.from.length - 2) {
								suffix = " or ";
							} else if (j < ch.from.length - 2) {
								suffix = ", ";
							}
						}
						let thsAmount = ` ${amount}`;
						if (ch.from.length > 1) {
							if (j !== ch.from.length - 1) {
								thsAmount = "";
							}
						}
						outStack += ch.from[j].uppercaseFirst() + thsAmount + suffix;
					}
				}
			}

			if (outStack.trim()) {
				toConvertToText.push(`Choose ${outStack}`);
				toConvertToShortText.push(outStack.uppercaseFirst());
			}
		}
	}

	function isAllAbilitiesWithParent (chooseAbs) {
		const tempAbilities = [];
		for (let i = 0; i < mainAbs.length; ++i) {
			tempAbilities.push(mainAbs[i].toLowerCase());
		}
		for (let i = 0; i < chooseAbs.from.length; ++i) {
			const ab = chooseAbs.from[i].toLowerCase();
			if (!tempAbilities.includes(ab)) tempAbilities.push(ab);
			if (!asCollection.includes(ab.toLowerCase)) asCollection.push(ab.toLowerCase());
		}
		return tempAbilities.length === 6;
	}
};

Renderer._AbilityData = function ({asText, asTextShort, asCollection, areNegative} = {}) {
	this.asText = asText || "";
	this.asTextShort = asTextShort || "";
	this.asCollection = asCollection || [];
	this.areNegative = areNegative || [];
};

/**
 * @param filters String of the form `"level=1;2|class=Warlock"`
 * @param namespace Filter namespace to use
 */
Renderer.getFilterSubhashes = function (filters, namespace = null) {
	let customHash = null;

	const subhashes = filters.map(f => {
		const [fName, fVals, fMeta, fOpts] = f.split("=").map(s => s.trim());
		const isBoxData = fName.startsWith("fb");
		const key = isBoxData ? `${fName}${namespace ? `.${namespace}` : ""}` : `flst${namespace ? `.${namespace}` : ""}${UrlUtil.encodeForHash(fName)}`;

		let value;
		// special cases for "search" and "hash" keywords
		if (isBoxData) {
			return {
				key,
				value: fVals,
				preEncoded: true,
			};
		} else if (fName === "search") {
			// "search" as a filter name is hackily converted to a box meta option
			return {
				key: VeCt.FILTER_BOX_SUB_HASH_SEARCH_PREFIX,
				value: UrlUtil.encodeForHash(fVals),
				preEncoded: true,
			};
		} else if (fName === "hash") {
			customHash = fVals;
			return null;
		} else if (fVals.startsWith("[") && fVals.endsWith("]")) { // range
			const [min, max] = fVals.substring(1, fVals.length - 1).split(";").map(it => it.trim());
			if (max == null) { // shorthand version, with only one value, becomes min _and_ max
				value = [
					`min=${min}`,
					`max=${min}`,
				].join(HASH_SUB_LIST_SEP);
			} else {
				value = [
					min ? `min=${min}` : "",
					max ? `max=${max}` : "",
				].filter(Boolean).join(HASH_SUB_LIST_SEP);
			}
		} else if (fVals.startsWith("::") && fVals.endsWith("::")) { // options
			value = fVals.substring(2, fVals.length - 2).split(";")
				.map(it => it.trim())
				.map(it => {
					if (it.startsWith("!")) return `${UrlUtil.encodeForHash(it.slice(1))}=${UrlUtil.mini.compress(false)}`;
					return `${UrlUtil.encodeForHash(it)}=${UrlUtil.mini.compress(true)}`;
				})
				.join(HASH_SUB_LIST_SEP);
		} else {
			value = fVals.split(";")
				.map(s => s.trim())
				.filter(Boolean)
				.map(s => {
					if (s.startsWith("!")) return `${UrlUtil.encodeForHash(s.slice(1))}=2`;
					return `${UrlUtil.encodeForHash(s)}=1`;
				})
				.join(HASH_SUB_LIST_SEP);
		}

		const out = [{
			key,
			value,
			preEncoded: true,
		}];

		if (fMeta) {
			out.push({
				key: `flmt${UrlUtil.encodeForHash(fName)}`,
				value: fMeta,
				preEncoded: true,
			});
		}

		if (fOpts) {
			out.push({
				key: `flop${UrlUtil.encodeForHash(fName)}`,
				value: fOpts,
				preEncoded: true,
			});
		}

		return out;
	}).flat().filter(Boolean);

	return {
		customHash,
		subhashes,
	};
};

Renderer.song = class {
	static getCompactRenderedString (ent) {
		const src = ent._img.face;
		return `<div class="ve-flex-h-center">
				<img style="max-width: 100%; max-height: 100%" src="${src}" alt="?">
			</div>`;
	}

	static getRenderedString (ent, {isBack = false} = {}) {
		const src = isBack ? ent._img.back : ent._img.face;
		const renderer = Renderer.get();
		const stack = [`<div class="ve-flex-h-center">
				<img style="max-height: 400px; max-width: 100%" src="${src}" alt="?">
			</div>`];
		if (!isBack && ent.statistics.commander && ent.tactics.cards) {
			const tacticsNote = renderer.render(`{@note Tactics cards: ${Object.entries(ent.tactics.cards).map(([id, name]) => `{@tactics ${id}|${ent.lang}|${name}}`).join(", ")}}`);
			stack.push(`<div class="m-2">${tacticsNote}</div>`);
		} else if (ent.__prop === "tactics" && ent.statistics.commander_id) {
			const cmdrNote = renderer.render(`{@note Commander: {@attachments ${ent.statistics.commander_id}|${ent.lang}|${ent.statistics.commander_name}}}`)
			stack.push(`<div class="m-2">${cmdrNote}</div>`);
		}
		return stack.join("");
	}

	static getRealSize_mm (ent) {
		switch (ent.__prop) {
			case "units": return {w: 120, h: 70}
			case "attachments":
			case "tactics":
			case "ncus": return {w: 64, h: 90}
		}
	}
};
Renderer.utils = class {
	static isDisplayPage (page) { return page != null && ((!isNaN(page) && page > 0) || isNaN(page)); }

	static TabButton = function ({label, fnChange, fnPopulate, isVisible}) {
		this.label = label;
		this.fnChange = fnChange;
		this.fnPopulate = fnPopulate;
		this.isVisible = isVisible;
	};

	static _tabs = {};
	static _curTab = null;
	static _tabsPreferredLabel = null;
	static bindTabButtons ({tabButtons, tabLabelReference, $wrpTabs, $pgContent}) {
		Renderer.utils._tabs = {};
		Renderer.utils._curTab = null;

		$wrpTabs.find(`.stat-tab-gen`).remove();

		tabButtons.forEach((tb, i) => {
			tb.ix = i;

			tb.$t = $(`<button class="ui-tab__btn-tab-head btn btn-default stat-tab-gen">${tb.label}</button>`)
				.click(() => tb.fnActivateTab({isUserInput: true}));

			tb.fnActivateTab = ({isUserInput = false} = {}) => {
				const curTab = Renderer.utils._curTab;
				const tabs = Renderer.utils._tabs;

				if (!curTab || curTab.label !== tb.label) {
					if (curTab) curTab.$t.removeClass(`ui-tab__btn-tab-head--active`);
					Renderer.utils._curTab = tb;
					tb.$t.addClass(`ui-tab__btn-tab-head--active`);
					if (curTab) tabs[curTab.label].$content = $pgContent.children().detach();

					tabs[tb.label] = tb;
					if (!tabs[tb.label].$content && tb.fnPopulate) tb.fnPopulate();
					else $pgContent.append(tabs[tb.label].$content);
					if (tb.fnChange) tb.fnChange();
				}

				// If the user clicked a tab, save it as their chosen tab
				if (isUserInput) Renderer.utils._tabsPreferredLabel = tb.label;
			};
		});

		// Avoid displaying a tab button for single tabs
		if (tabButtons.length !== 1) tabButtons.slice().reverse().forEach(tb => $wrpTabs.prepend(tb.$t));

		// If there was no previous selection, select the first tab
		if (!Renderer.utils._tabsPreferredLabel) return tabButtons[0].fnActivateTab();

		// If the exact tab exist, select it
		const tabButton = tabButtons.find(tb => tb.label === Renderer.utils._tabsPreferredLabel);
		if (tabButton) return tabButton.fnActivateTab();

		// If the user's preferred tab is not present, find the closest tab, and activate it instead.
		// Always prefer later tabs.
		const ixDesired = tabLabelReference.indexOf(Renderer.utils._tabsPreferredLabel);
		if (!~ixDesired) return tabButtons[0].fnActivateTab(); // Should never occur

		const ixsAvailableMetas = tabButtons
			.map(tb => {
				const ixMapped = tabLabelReference.indexOf(tb.label);
				if (!~ixMapped) return null;
				return {
					ixMapped,
					label: tb.label,
				};
			})
			.filter(Boolean);
		if (!ixsAvailableMetas.length) return tabButtons[0].fnActivateTab(); // Should never occur

		// Find a later tab and activate it, if possible
		const ixMetaHigher = ixsAvailableMetas.find(({ixMapped}) => ixMapped > ixDesired);
		if (ixMetaHigher != null) return (tabButtons.find(it => it.label === ixMetaHigher.label) || tabButtons[0]).fnActivateTab();

		// Otherwise, click the highest tab
		const ixMetaMax = ixsAvailableMetas.last();
		(tabButtons.find(it => it.label === ixMetaMax.label) || tabButtons[0]).fnActivateTab();
	}

	static getEntryMediaUrl (entry, prop, mediaDir) {
		if (!entry[prop]) return "";

		let href = "";
		if (entry[prop].type === "internal") {
			href = UrlUtil.link(Renderer.get().getMediaUrl(mediaDir, entry[prop].path));
		} else if (entry[prop].type === "external") {
			href = entry[prop].url;
		}
		return href;
	}

	static getTagEntry (tag, text) {
		switch (tag) {
			case "@dice":
			case "@autodice":
			case "@damage":
			case "@hit":
			case "@d20":
			case "@chance":
			case "@recharge": {
				const fauxEntry = {
					type: "dice",
					rollable: true,
				};
				const [rollText, displayText, name, ...others] = Renderer.splitTagByPipe(text);
				if (displayText) fauxEntry.displayText = displayText;

				if ((!fauxEntry.displayText && (rollText || "").includes("summonSpellLevel")) || (fauxEntry.displayText && fauxEntry.displayText.includes("summonSpellLevel"))) fauxEntry.displayText = (fauxEntry.displayText || rollText || "").replace(/summonSpellLevel/g, "the spell's level");

				if ((!fauxEntry.displayText && (rollText || "").includes("summonClassLevel")) || (fauxEntry.displayText && fauxEntry.displayText.includes("summonClassLevel"))) fauxEntry.displayText = (fauxEntry.displayText || rollText || "").replace(/summonClassLevel/g, "your class level");

				if (name) fauxEntry.name = name;

				switch (tag) {
					case "@dice":
					case "@autodice":
					case "@damage": {
						// format: {@dice 1d2 + 3 + 4d5 - 6}
						fauxEntry.toRoll = rollText;

						if (!fauxEntry.displayText && (rollText || "").includes(";")) fauxEntry.displayText = rollText.replace(/;/g, "/");
						if ((!fauxEntry.displayText && (rollText || "").includes("#$")) || (fauxEntry.displayText && fauxEntry.displayText.includes("#$"))) fauxEntry.displayText = (fauxEntry.displayText || rollText).replace(/#\$prompt_number[^$]*\$#/g, "(n)");
						fauxEntry.displayText = fauxEntry.displayText || fauxEntry.toRoll;

						if (tag === "@damage") fauxEntry.subType = "damage";
						if (tag === "@autodice") fauxEntry.autoRoll = true;

						return fauxEntry;
					}
					case "@d20":
					case "@hit": {
						// format: {@hit +1} or {@hit -2}
						let mod;
						if (!isNaN(rollText)) {
							const n = Number(rollText);
							mod = `${n >= 0 ? "+" : ""}${n}`;
						} else mod = /^\s+[-+]/.test(rollText) ? rollText : `+${rollText}`;
						fauxEntry.displayText = fauxEntry.displayText || mod;
						fauxEntry.toRoll = `1d20${mod}`;
						fauxEntry.subType = "d20";
						fauxEntry.d20mod = mod;
						if (tag === "@hit") fauxEntry.context = {type: "hit"};
						return fauxEntry;
					}
					case "@chance": {
						// format: {@chance 25|display text|rollbox rollee name|success text|failure text}
						const [textSuccess, textFailure] = others;
						fauxEntry.toRoll = `1d100`;
						fauxEntry.successThresh = Number(rollText);
						fauxEntry.chanceSuccessText = textSuccess;
						fauxEntry.chanceFailureText = textFailure;
						return fauxEntry;
					}
					case "@recharge": {
						// format: {@recharge 4|flags}
						const flags = displayText ? displayText.split("") : null; // "m" for "minimal" = no brackets
						fauxEntry.toRoll = "1d6";
						const asNum = Number(rollText || 6);
						fauxEntry.successThresh = 7 - asNum;
						fauxEntry.successMax = 6;
						fauxEntry.displayText = `${asNum}${asNum < 6 ? `\u20136` : ""}`;
						fauxEntry.chanceSuccessText = "Recharged!";
						fauxEntry.chanceFailureText = "Did not recharge";
						fauxEntry.isColorSuccessFail = true;
						return fauxEntry;
					}
				}

				return fauxEntry;
			}

			case "@ability": // format: {@ability str 20} or {@ability str 20|Display Text} or {@ability str 20|Display Text|Roll Name Text}
			case "@savingThrow": { // format: {@savingThrow str 5} or {@savingThrow str 5|Display Text} or {@savingThrow str 5|Display Text|Roll Name Text}
				const fauxEntry = {
					type: "dice",
					rollable: true,
					subType: "d20",
					context: {type: tag === "@ability" ? "abilityCheck" : "savingThrow"},
				};

				const [abilAndScoreOrScore, displayText, name, ...others] = Renderer.splitTagByPipe(text);

				let [abil, ...rawScoreOrModParts] = abilAndScoreOrScore.split(" ").map(it => it.trim()).filter(Boolean);
				abil = abil.toLowerCase();

				fauxEntry.context.ability = abil;

				if (name) fauxEntry.name = name;
				else {
					if (tag === "@ability") fauxEntry.name = Parser.attAbvToFull(abil);
					else if (tag === "@savingThrow") fauxEntry.name = `${Parser.attAbvToFull(abil)} save`;
				}

				const rawScoreOrMod = rawScoreOrModParts.join(" ");
				// Saving throws can have e.g. `+ PB`
				if (isNaN(rawScoreOrMod) && tag === "@savingThrow") {
					if (displayText) fauxEntry.displayText = displayText;
					else fauxEntry.displayText = rawScoreOrMod;

					fauxEntry.toRoll = `1d20${rawScoreOrMod}`;
					fauxEntry.d20mod = rawScoreOrMod;
				} else {
					const scoreOrMod = Number(rawScoreOrMod) || 0;
					const mod = (tag === "@ability" ? Parser.getAbilityModifier : UiUtil.intToBonus)(scoreOrMod);

					if (displayText) fauxEntry.displayText = displayText;
					else {
						if (tag === "@ability") fauxEntry.displayText = `${scoreOrMod} (${mod})`;
						else fauxEntry.displayText = mod;
					}

					fauxEntry.toRoll = `1d20${mod}`;
					fauxEntry.d20mod = mod;
				}

				return fauxEntry;
			}

			// format: {@skillCheck animal_handling 5} or {@skillCheck animal_handling 5|Display Text}
			//   or {@skillCheck animal_handling 5|Display Text|Roll Name Text}
			case "@skillCheck": {
				const fauxEntry = {
					type: "dice",
					rollable: true,
					subType: "d20",
					context: {type: "skillCheck"},
				};

				const [skillAndMod, displayText, name, ...others] = Renderer.splitTagByPipe(text);

				const parts = skillAndMod.split(" ").map(it => it.trim()).filter(Boolean);
				const namePart = parts.shift();
				const bonusPart = parts.join(" ");
				const skill = namePart.replace(/_/g, " ");

				let mod = bonusPart;
				if (!isNaN(bonusPart)) mod = UiUtil.intToBonus(Number(bonusPart) || 0);
				else if (bonusPart.startsWith("#$")) mod = `+${bonusPart}`;

				fauxEntry.context.skill = skill;
				fauxEntry.displayText = displayText || mod;

				if (name) fauxEntry.name = name;
				else fauxEntry.name = skill.toTitleCase();

				fauxEntry.toRoll = `1d20${mod}`;
				fauxEntry.d20mod = mod;

				return fauxEntry;
			}

			// format: {@coinflip} or {@coinflip display text|rollbox rollee name|success text|failure text}
			case "@coinflip": {
				const [displayText, name, textSuccess, textFailure] = Renderer.splitTagByPipe(text);

				const fauxEntry = {
					type: "dice",
					toRoll: "1d2",
					successThresh: 1,
					successMax: 2,
					displayText: displayText || "flip a coin",
					chanceSuccessText: textSuccess || `Heads`,
					chanceFailureText: textFailure || `Tails`,
					isColorSuccessFail: !textSuccess && !textFailure,
					rollable: true,
				};

				return fauxEntry;
			}

			default: throw new Error(`Unhandled tag "${tag}"`);
		}
	}

	static getTagMeta (tag, text) {
		switch (tag) {
			case "@attachments":
			case "@units":
			case "@ncus":
			case "@tactics":
			case "@song": {
				let [id, source, displayText, ...others] = Renderer.splitTagByPipe(text);
				source = source || Parser.SRC_EN;
				const hash = UrlUtil.URL_TO_HASH_BUILDER[UrlUtil.PG_SONG]({id, source});
				return {
					name: id,
					displayText,
					others,

					page: UrlUtil.PG_SONG,
					source,
					hash,

					hashPreEncoded: true,
				};
			}
			default: return Renderer.utils._getTagMeta_generic(tag, text);
		}
	}

	static _getTagMeta_generic (tag, text) {
		const {name, source, displayText, others} = DataUtil.generic.unpackUid(text, tag);
		const hash = UrlUtil.encodeForHash([name, source]);

		const out = {
			name,
			displayText,
			others,

			page: null,
			source,
			hash,

			preloadId: null,
			subhashes: null,
			linkText: null,

			hashPreEncoded: true,
		};

		switch (tag) {
			case "@cite": { out.isFauxPage = true; out.page = "citation"; break; }

			default: throw new Error(`Unhandled tag "${tag}"`);
		}

		return out;
	}

	static getLinkSubhashString (subhashes) {
		let out = "";
		const len = subhashes.length;
		for (let i = 0; i < len; ++i) {
			const subHash = subhashes[i];
			if (subHash.preEncoded) out += `${HASH_PART_SEP}${subHash.key}${HASH_SUB_KV_SEP}`;
			else out += `${HASH_PART_SEP}${UrlUtil.encodeForHash(subHash.key)}${HASH_SUB_KV_SEP}`;
			if (subHash.value != null) {
				if (subHash.preEncoded) out += subHash.value;
				else out += UrlUtil.encodeForHash(subHash.value);
			} else {
				// TODO allow list of values
				out += subHash.values.map(v => UrlUtil.encodeForHash(v)).join(HASH_SUB_LIST_SEP);
			}
		}
		return out;
	}

	static lazy = {
		_getIntersectionConfig () {
			return {
				rootMargin: "150px 0px", // if the element gets within 150px of the viewport
				threshold: 0.01,
			};
		},

		_OBSERVERS: {},
		getCreateObserver ({observerId, fnOnObserve}) {
			if (!Renderer.utils.lazy._OBSERVERS[observerId]) {
				const observer = Renderer.utils.lazy._OBSERVERS[observerId] = new IntersectionObserver(
					Renderer.utils.lazy.getFnOnIntersect({
						observerId,
						fnOnObserve,
					}),
					Renderer.utils.lazy._getIntersectionConfig(),
				);

				observer._TRACKED = new Set();

				observer.track = it => {
					observer._TRACKED.add(it);
					return observer.observe(it);
				};

				observer.untrack = it => {
					observer._TRACKED.delete(it);
					return observer.unobserve(it);
				};

				// If we try to print a page with e.g. un-loaded images, attempt to load them all first
				observer._printListener = evt => {
					if (!observer._TRACKED.size) return;

					// region Sadly we cannot cancel or delay the print event, so, show a blocking alert
					[...observer._TRACKED].forEach(it => {
						observer.untrack(it);
						fnOnObserve({
							observer,
							entry: {
								target: it,
							},
						});
					});

					alert(`All content must be loaded prior to printing. Please cancel the print and wait a few moments for loading to complete!`);
					// endregion
				};
				window.addEventListener("beforeprint", observer._printListener);
			}
			return Renderer.utils.lazy._OBSERVERS[observerId];
		},

		destroyObserver ({observerId}) {
			const observer = Renderer.utils.lazy._OBSERVERS[observerId];
			if (!observer) return;

			observer.disconnect();
			window.removeEventListener("beforeprint", observer._printListener);
		},

		getFnOnIntersect ({observerId, fnOnObserve}) {
			return obsEntries => {
				const observer = Renderer.utils.lazy._OBSERVERS[observerId];

				obsEntries.forEach(entry => {
					// filter observed entries for those that intersect
					if (entry.intersectionRatio <= 0) return;

					observer.untrack(entry.target);
					fnOnObserve({
						observer,
						entry,
					});
				});
			};
		},
	};
};

Renderer.tag = class {
	static _TagBase = class {
		tagName;
		defaultSource = null;
		page = null;

		get tag () { return `@${this.tagName}`; }

		getStripped (tag, text) {
			text = DataUtil.generic.variableResolver.getHumanReadableString(text); // replace any variables
			return this._getStripped(tag, text);
		}

		/** @abstract */
		_getStripped (tag, text) { throw new Error("Unimplemented!"); }

		getMeta (tag, text) { return this._getMeta(tag, text); }
		_getMeta (tag, text) { throw new Error("Unimplemented!"); }
	};

	static _TagBaseAt = class extends this._TagBase {
		get tag () { return `@${this.tagName}`; }
	};

	static _TagBaseHash = class extends this._TagBase {
		get tag () { return `#${this.tagName}`; }
	};

	static _TagTextStyle = class extends this._TagBaseAt {
		_getStripped (tag, text) { return text; }
	};

	static TagBoldShort = class extends this._TagTextStyle {
		tagName = "b";
	};

	static TagBoldLong = class extends this._TagTextStyle {
		tagName = "bold";
	};

	static TagItalicShort = class extends this._TagTextStyle {
		tagName = "i";
	};

	static TagItalicLong = class extends this._TagTextStyle {
		tagName = "italic";
	};

	static TagStrikethroughShort = class extends this._TagTextStyle {
		tagName = "s";
	};

	static TagStrikethroughLong = class extends this._TagTextStyle {
		tagName = "strike";
	};

	static TagStrikethroughDoubleShort = class extends this._TagTextStyle {
		tagName = "s2";
	};

	static TagStrikethroughDoubleLong = class extends this._TagTextStyle {
		tagName = "strikeDouble";
	};

	static TagUnderlineShort = class extends this._TagTextStyle {
		tagName = "u";
	};

	static TagUnderlineLong = class extends this._TagTextStyle {
		tagName = "underline";
	};

	static TagUnderlineDoubleShort = class extends this._TagTextStyle {
		tagName = "u2";
	};

	static TagUnderlineDoubleLong = class extends this._TagTextStyle {
		tagName = "underlineDouble";
	};

	static TagSup = class extends this._TagTextStyle {
		tagName = "sup";
	};

	static TagSub = class extends this._TagTextStyle {
		tagName = "sub";
	};

	static TagKbd = class extends this._TagTextStyle {
		tagName = "kbd";
	};

	static TagCode = class extends this._TagTextStyle {
		tagName = "code";
	};

	static TagStyle = class extends this._TagTextStyle {
		tagName = "style";
	};

	static TagFont = class extends this._TagTextStyle {
		tagName = "font";
	};

	static TagComic = class extends this._TagTextStyle {
		tagName = "comic";
	};

	static TagComicH1 = class extends this._TagTextStyle {
		tagName = "comicH1";
	};

	static TagComicH2 = class extends this._TagTextStyle {
		tagName = "comicH2";
	};

	static TagComicH3 = class extends this._TagTextStyle {
		tagName = "comicH3";
	};

	static TagComicH4 = class extends this._TagTextStyle {
		tagName = "comicH4";
	};

	static TagComicNote = class extends this._TagTextStyle {
		tagName = "comicNote";
	};

	static TagNote = class extends this._TagTextStyle {
		tagName = "note";
	};

	static TagTip = class extends this._TagTextStyle {
		tagName = "tip";
	};

	static _TagPipedNoDisplayText = class extends this._TagBaseAt {
		_getStripped (tag, text) {
			const parts = Renderer.splitTagByPipe(text);
			return parts[0];
		}
	};

	static TagFilter = class extends this._TagPipedNoDisplayText {
		tagName = "filter";
	};
	static TagLink = class extends this._TagPipedNoDisplayText {
		tagName = "link";
	};

	static TagLoader = class extends this._TagPipedNoDisplayText {
		tagName = "loader";
	};

	static TagColor = class extends this._TagPipedNoDisplayText {
		tagName = "color";
	};

	static TagHighlight = class extends this._TagPipedNoDisplayText {
		tagName = "highlight";
	};

	static TagHelp = class extends this._TagPipedNoDisplayText {
		tagName = "help";
	};

	static _TagPipedDisplayTextThird = class extends this._TagBaseAt {
		_getStripped (tag, text) {
			const parts = Renderer.splitTagByPipe(text);
			return parts.length >= 3 ? parts[2] : parts[0];
		}
	};

	static TagAttachments = class extends this._TagPipedDisplayTextThird {
		tagName = "attachments";
		defaultSource = "en";
		page = UrlUtil.PG_SONG;
	};

	static TagHomebrew = class extends this._TagBaseAt {
		tagName = "homebrew";

		_getStripped (tag, text) {
			const [newText, oldText] = Renderer.splitTagByPipe(text);
			if (newText && oldText) {
				return `${newText} [this is a homebrew addition, replacing the following: "${oldText}"]`;
			} else if (newText) {
				return `${newText} [this is a homebrew addition]`;
			} else if (oldText) {
				return `[the following text has been removed due to homebrew: ${oldText}]`;
			} else throw new Error(`Homebrew tag had neither old nor new text!`);
		}
	};

	/* -------------------------------------------- */

	static TAGS = [
		new this.TagBoldShort(),
		new this.TagBoldLong(),
		new this.TagItalicShort(),
		new this.TagItalicLong(),
		new this.TagStrikethroughShort(),
		new this.TagStrikethroughLong(),
		new this.TagStrikethroughDoubleShort(),
		new this.TagStrikethroughDoubleLong(),
		new this.TagUnderlineShort(),
		new this.TagUnderlineLong(),
		new this.TagUnderlineDoubleShort(),
		new this.TagUnderlineDoubleLong(),
		new this.TagSup(),
		new this.TagSub(),
		new this.TagKbd(),
		new this.TagCode(),
		new this.TagStyle(),
		new this.TagFont(),

		new this.TagComic(),
		new this.TagComicH1(),
		new this.TagComicH2(),
		new this.TagComicH3(),
		new this.TagComicH4(),
		new this.TagComicNote(),

		new this.TagNote(),
		new this.TagTip(),

		new this.TagAttachments(),


		new this.TagFilter(),
		new this.TagLink(),
		new this.TagLoader(),
		new this.TagColor(),
		new this.TagHighlight(),
		new this.TagHelp(),

		new this.TagHomebrew(),
	];

	static TAG_LOOKUP = {};

	static _init () {
		this.TAGS.forEach(tag => {
			this.TAG_LOOKUP[tag.tag] = tag;
			this.TAG_LOOKUP[tag.tagName] = tag;
		});

		return null;
	}

	static _ = this._init();

	/* ----------------------------------------- */

	static getPage (tag) {
		const tagInfo = this.TAG_LOOKUP[tag];
		return tagInfo?.page;
	}
};

Renderer.events = class {
	static handleClick_copyCode (evt, ele) {
		const $e = $(ele).parent().next("pre");
		MiscUtil.pCopyTextToClipboard($e.text());
		JqueryUtil.showCopiedEffect($e);
	}

	static handleClick_toggleCodeWrap (evt, ele) {
		const nxt = !StorageUtil.syncGet("rendererCodeWrap");
		StorageUtil.syncSet("rendererCodeWrap", nxt);
		const $btn = $(ele).toggleClass("active", nxt);
		const $e = $btn.parent().next("pre");
		$e.toggleClass("rd__pre-wrap", nxt);
	}

	static bindGeneric ({element = document.body} = {}) {
		const $ele = $(element);

		Renderer.events._HEADER_TOGGLE_CLICK_SELECTORS
			.forEach(selector => {
				$ele
					.on("click", selector, evt => {
						Renderer.events.handleClick_headerToggleButton(evt, evt.currentTarget, {selector});
					});
			})
		;
	}

	static _HEADER_TOGGLE_CLICK_SELECTORS = [
		`[data-rd-h-toggle-button]`,
		`[data-rd-h-special-toggle-button]`,
	];

	static handleClick_headerToggleButton (evt, ele, {selector = false} = {}) {
		evt.stopPropagation();
		evt.preventDefault();

		const isShow = this._handleClick_headerToggleButton_doToggleEle(ele, {selector});

		if (!EventUtil.isCtrlMetaKey(evt)) return;

		Renderer.events._HEADER_TOGGLE_CLICK_SELECTORS
			.forEach(selector => {
				[...document.querySelectorAll(selector)]
					.filter(eleOther => eleOther !== ele)
					.forEach(eleOther => {
						Renderer.events._handleClick_headerToggleButton_doToggleEle(eleOther, {selector, force: isShow});
					});
			})
		;
	}

	static _handleClick_headerToggleButton_doToggleEle (ele, {selector = false, force = null} = {}) {
		const isShow = force != null ? force : ele.innerHTML.includes("+");

		let eleNxt = ele.closest(".rd__h").nextElementSibling;

		while (eleNxt) {
			// Never hide float-fixing elements
			if (eleNxt.classList.contains("float-clear")) {
				eleNxt = eleNxt.nextElementSibling;
				continue;
			}

			// For special sections, always collapse the whole thing.
			if (selector !== `[data-rd-h-special-toggle-button]`) {
				const eleToCheck = Renderer.events._handleClick_headerToggleButton_getEleToCheck(eleNxt);
				if (
					eleToCheck.classList.contains("rd__b-special")
					|| (eleToCheck.classList.contains("rd__h") && !eleToCheck.classList.contains("rd__h--3"))
					|| (eleToCheck.classList.contains("rd__b") && !eleToCheck.classList.contains("rd__b--3"))
				) break;
			}

			eleNxt.classList.toggle("rd__ele-toggled-hidden", !isShow);
			eleNxt = eleNxt.nextElementSibling;
		}

		ele.innerHTML = isShow ? "[\u2013]" : "[+]";

		return isShow;
	}

	static _handleClick_headerToggleButton_getEleToCheck (eleNxt) {
		if (eleNxt.type === 3) return eleNxt; // Text nodes

		// If the element is a block with only one child which is itself a block, treat it as a "wrapper" block, and dig
		if (!eleNxt.classList.contains("rd__b") || eleNxt.classList.contains("rd__b--3")) return eleNxt;
		const childNodes = [...eleNxt.childNodes].filter(it => (it.type === 3 && (it.textContent || "").trim()) || it.type !== 3);
		if (childNodes.length !== 1) return eleNxt;
		if (childNodes[0].classList.contains("rd__b")) return Renderer.events._handleClick_headerToggleButton_getEleToCheck(childNodes[0]);
		return eleNxt;
	}
};

Renderer.hover = class {
	static LinkMeta = class {
		constructor () {
			this.isHovered = false;
			this.isLoading = false;
			this.isPermanent = false;
			this.windowMeta = null;
		}
	};

	static _BAR_HEIGHT = 16;

	static _linkCache = {};
	static _eleCache = new Map();
	static _entryCache = {};
	static _isInit = false;
	static _lastId = 0;
	static _contextMenu = null;
	static _contextMenuLastClicked = null;

	static _getNextId () { return ++Renderer.hover._lastId; }

	static _doInit () {
		if (!Renderer.hover._isInit) {
			Renderer.hover._isInit = true;

			$(document.body).on("click", () => Renderer.hover.cleanTempWindows());

			Renderer.hover._contextMenu = ContextUtil.getMenu([
				new ContextUtil.Action(
					"Maximize All",
					() => {
						const $permWindows = $(`.hoverborder[data-perm="true"]`);
						$permWindows.attr("data-display-title", "false");
					},
				),
				new ContextUtil.Action(
					"Minimize All",
					() => {
						const $permWindows = $(`.hoverborder[data-perm="true"]`);
						$permWindows.attr("data-display-title", "true");
					},
				),
				null,
				new ContextUtil.Action(
					"Close Others",
					() => {
						const hoverId = Renderer.hover._contextMenuLastClicked?.hoverId;
						Renderer.hover._doCloseAllWindows({hoverIdBlocklist: new Set([hoverId])});
					},
				),
				new ContextUtil.Action(
					"Close All",
					() => Renderer.hover._doCloseAllWindows(),
				),
			]);
		}
	}

	static cleanTempWindows () {
		for (const [key, meta] of Renderer.hover._eleCache.entries()) {
			// If this is an element-less "permanent" show (i.e. a "predefined" window) which has been closed
			if (!meta.isPermanent && meta.windowMeta && typeof key === "number") {
				meta.windowMeta.doClose();
				Renderer.hover._eleCache.delete(key);
				continue;
			}

			if (!meta.isPermanent && meta.windowMeta && !document.body.contains(key)) {
				meta.windowMeta.doClose();
				continue;
			}

			if (!meta.isPermanent && meta.isHovered && meta.windowMeta) {
				// Check if any elements have failed to clear their hovering status on mouse move
				const bounds = key.getBoundingClientRect();
				if (EventUtil._mouseX < bounds.x
					|| EventUtil._mouseY < bounds.y
					|| EventUtil._mouseX > bounds.x + bounds.width
					|| EventUtil._mouseY > bounds.y + bounds.height) {
					meta.windowMeta.doClose();
				}
			}
		}
	}

	static _doCloseAllWindows ({hoverIdBlocklist = null} = {}) {
		Object.entries(Renderer.hover._WINDOW_METAS)
			.filter(([hoverId, meta]) => hoverIdBlocklist == null || !hoverIdBlocklist.has(Number(hoverId)))
			.forEach(([, meta]) => meta.doClose());
	}

	static _getSetMeta (key) {
		if (!Renderer.hover._eleCache.has(key)) Renderer.hover._eleCache.set(key, new Renderer.hover.LinkMeta());
		return Renderer.hover._eleCache.get(key);
	}

	static _handleGenericMouseOverStart ({evt, ele}) {
		// Don't open on small screens unless forced
		if (Renderer.hover.isSmallScreen(evt) && !evt.shiftKey) return;

		Renderer.hover.cleanTempWindows();

		const meta = Renderer.hover._getSetMeta(ele);
		if (meta.isHovered || meta.isLoading) return; // Another hover is already in progress

		// Set the cursor to a waiting spinner
		ele.style.cursor = "progress";

		meta.isHovered = true;
		meta.isLoading = true;
		meta.isPermanent = evt.shiftKey;

		return meta;
	}

	static _doPredefinedShowStart ({entryId}) {
		Renderer.hover.cleanTempWindows();

		const meta = Renderer.hover._getSetMeta(entryId);

		meta.isPermanent = true;

		return meta;
	}

	static getLinkElementData (ele) {
		return {
			page: ele.dataset.vetPage,
			source: ele.dataset.vetSource,
			hash: ele.dataset.vetHash,
			preloadId: ele.dataset.vetPreloadId,
			isFauxPage: ele.dataset.vetIsFauxPage,
		};
	}

	// (Baked into render strings)
	static async pHandleLinkMouseOver (evt, ele, opts) {
		Renderer.hover._doInit();

		let page, source, hash, preloadId, customHashId, isFauxPage;
		if (opts) {
			page = opts.page;
			source = opts.source;
			hash = opts.hash;
			preloadId = opts.preloadId;
			customHashId = opts.customHashId;
			isFauxPage = !!opts.isFauxPage;
		} else {
			({
				page,
				source,
				hash,
				preloadId,
				isFauxPage,
			} = Renderer.hover.getLinkElementData(ele));
		}

		let meta = Renderer.hover._handleGenericMouseOverStart({evt, ele});
		if (meta == null) return;

		const toRender = await DataLoader.pCacheAndGet(page, source, hash);

		meta.isLoading = false;

		if (opts?.isDelay) {
			meta.isDelayed = true;
			ele.style.cursor = "help";
			await MiscUtil.pDelay(1100);
			meta.isDelayed = false;
		}

		// Reset cursor
		ele.style.cursor = "";

		// Check if we're still hovering the entity
		if (!meta || (!meta.isHovered && !meta.isPermanent)) return;

		const tmpEvt = meta._tmpEvt;
		delete meta._tmpEvt;

		// TODO(Future) avoid rendering e.g. creature scaling controls if `win?._IS_POPOUT`
		const win = (evt.view || {}).window;

		const $content = Renderer.hover.$getHoverContent_stats(page, toRender);

		// FIXME(Future) replace this with something maintainable
		const compactReferenceData = {
			page,
			source,
			hash,
		};

		if (meta.windowMeta && !meta.isPermanent) {
			meta.windowMeta.doClose();
			meta.windowMeta = null;
		}

		meta.windowMeta = Renderer.hover.getShowWindow(
			$content,
			Renderer.hover.getWindowPositionFromEvent(tmpEvt || evt, {isPreventFlicker: !meta.isPermanent}),
			{
				title: toRender ? toRender.name : "",
				isPermanent: meta.isPermanent,
				pageUrl: isFauxPage ? null : `${Renderer.get().baseUrl}${page}#${hash}`,
				cbClose: () => meta.isHovered = meta.isPermanent = meta.isLoading = meta.isFluff = false,
				isBookContent: page === UrlUtil.PG_RECIPES,
				compactReferenceData,
				sourceData: toRender,
				width: Renderer.hover._getDefaultWidth(toRender)
			},
		);
	}

	// (Baked into render strings)
	static handleInlineMouseOver (evt, ele, entry, opts) {
		Renderer.hover._doInit();

		entry = entry || JSON.parse(ele.dataset.vetEntry);

		let meta = Renderer.hover._handleGenericMouseOverStart({evt, ele});
		if (meta == null) return;

		meta.isLoading = false;

		// Reset cursor
		ele.style.cursor = "";

		// Check if we're still hovering the entity
		if (!meta || (!meta.isHovered && !meta.isPermanent)) return;

		const tmpEvt = meta._tmpEvt;
		delete meta._tmpEvt;

		const win = (evt.view || {}).window;

		const $content = Renderer.hover.$getHoverContent_generic(entry, opts);

		if (meta.windowMeta && !meta.isPermanent) {
			meta.windowMeta.doClose();
			meta.windowMeta = null;
		}

		meta.windowMeta = Renderer.hover.getShowWindow(
			$content,
			Renderer.hover.getWindowPositionFromEvent(tmpEvt || evt, {isPreventFlicker: !meta.isPermanent}),
			{
				title: entry?.name || "",
				isPermanent: meta.isPermanent,
				pageUrl: null,
				cbClose: () => meta.isHovered = meta.isPermanent = meta.isLoading = false,
				isBookContent: true,
				sourceData: entry,
				width: Renderer.hover._getDefaultWidth(entry)
			},
		);
	}

	// (Baked into render strings)
	static handleLinkMouseLeave (evt, ele) {
		const meta = Renderer.hover._eleCache.get(ele);
		ele.style.cursor = "";

		if (!meta || meta.isPermanent) return;

		if (evt.shiftKey) {
			meta.isPermanent = true;
			meta.windowMeta.setIsPermanent(true);
			return;
		}

		meta.isHovered = false;
		if (meta.windowMeta) {
			meta.windowMeta.doClose();
			meta.windowMeta = null;
		}
	}

	// (Baked into render strings)
	static handleLinkMouseMove (evt, ele) {
		const meta = Renderer.hover._eleCache.get(ele);
		if (!meta || meta.isPermanent) return;

		// If loading has finished, but we're not displaying the element yet (e.g. because it has been delayed)
		if (meta.isDelayed) {
			meta._tmpEvt = evt;
			return;
		}

		if (!meta.windowMeta) return;

		meta.windowMeta.setPosition(Renderer.hover.getWindowPositionFromEvent(evt, {isPreventFlicker: !evt.shiftKey && !meta.isPermanent}));

		if (evt.shiftKey && !meta.isPermanent) {
			meta.isPermanent = true;
			meta.windowMeta.setIsPermanent(true);
		}
	}

	/**
	 * (Baked into render strings)
	 * @param evt
	 * @param ele
	 * @param entryId
	 * @param [opts]
	 * @param [opts.isBookContent]
	 * @param [opts.isLargeBookContent]
	 */
	static handlePredefinedMouseOver (evt, ele, entryId, opts) {
		opts = opts || {};

		const meta = Renderer.hover._handleGenericMouseOverStart({evt, ele});
		if (meta == null) return;

		Renderer.hover.cleanTempWindows();

		const toRender = Renderer.hover._entryCache[entryId];

		meta.isLoading = false;
		// Check if we're still hovering the entity
		if (!meta.isHovered && !meta.isPermanent) return;

		const $content = Renderer.hover.$getHoverContent_generic(toRender, opts);
		meta.windowMeta = Renderer.hover.getShowWindow(
			$content,
			Renderer.hover.getWindowPositionFromEvent(evt, {isPreventFlicker: !meta.isPermanent}),
			{
				title: toRender.data && toRender.data.hoverTitle != null ? toRender.data.hoverTitle : toRender.name,
				isPermanent: meta.isPermanent,
				cbClose: () => meta.isHovered = meta.isPermanent = meta.isLoading = false,
				sourceData: toRender,
				width: Renderer.hover._getDefaultWidth(toRender)
			},
		);

		// Reset cursor
		ele.style.cursor = "";
	}

	static handleLinkClick (evt, ele) {
		// Close the window (if not permanent)
		// Note that this prevents orphan windows when e.g. clicking a specific variant on an Items page magicvariant
		Renderer.hover.handleLinkMouseLeave(evt, ele);
	}

	// (Baked into render strings)
	static handleLinkDragStart (evt, ele) {
		// Close the window
		Renderer.hover.handleLinkMouseLeave(evt, ele);

		const {page, source, hash} = Renderer.hover.getLinkElementData(ele);
		const meta = {
			type: VeCt.DRAG_TYPE_IMPORT,
			page,
			source,
			hash,
		};
		evt.dataTransfer.setData("application/json", JSON.stringify(meta));
	}

	static _WINDOW_POSITION_PROPS_FROM_EVENT = [
		"isFromBottom",
		"isFromRight",
		"clientX",
		"window",
		"isPreventFlicker",
		"bcr",
	];

	static getWindowPositionFromEvent (evt, {isPreventFlicker = false} = {}) {
		const ele = evt.target;
		const win = evt?.view?.window || window;

		const bcr = ele.getBoundingClientRect().toJSON();

		const isFromBottom = bcr.top > win.innerHeight / 2;
		const isFromRight = bcr.left > win.innerWidth / 2;

		return {
			mode: "autoFromElement",
			isFromBottom,
			isFromRight,
			clientX: EventUtil.getClientX(evt),
			window: win,
			isPreventFlicker,
			bcr,
		};
	}

	static getWindowPositionExact (x, y, evt = null) {
		return {
			window: evt?.view?.window || window,
			mode: "exact",
			x,
			y,
		};
	}

	static _WINDOW_METAS = {};
	static MIN_Z_INDEX = 200;
	static _MAX_Z_INDEX = 300;
	static _DEFAULT_WIDTH_PX = 600;
	static _BODY_SCROLLER_WIDTH_PX = 15;

	static _getDefaultWidth (ent) {
		switch (ent.__prop) {
			case "attachments":
			case "tactics":
			case "ncus": return 300
			case "units": return 600
			default: return 600
		}
	}

	static _getZIndex () {
		const zIndices = Object.values(Renderer.hover._WINDOW_METAS).map(it => it.zIndex);
		if (!zIndices.length) return Renderer.hover.MIN_Z_INDEX;
		return Math.max(...zIndices);
	}

	static _getNextZIndex (hoverId) {
		const cur = Renderer.hover._getZIndex();
		// If we're already the highest index, continue to use this index
		if (hoverId != null && Renderer.hover._WINDOW_METAS[hoverId].zIndex === cur) return cur;
		// otherwise, go one higher
		const out = cur + 1;

		// If we've broken through the max z-index, try to free up some z-indices
		if (out > Renderer.hover._MAX_Z_INDEX) {
			const sortedWindowMetas = Object.entries(Renderer.hover._WINDOW_METAS)
				.sort(([kA, vA], [kB, vB]) => SortUtil.ascSort(vA.zIndex, vB.zIndex));

			if (sortedWindowMetas.length >= (Renderer.hover._MAX_Z_INDEX - Renderer.hover.MIN_Z_INDEX)) {
				// If we have too many window open, collapse them into one z-index
				sortedWindowMetas.forEach(([k, v]) => {
					v.setZIndex(Renderer.hover.MIN_Z_INDEX);
				});
			} else {
				// Otherwise, ensure one consistent run from min to max z-index
				sortedWindowMetas.forEach(([k, v], i) => {
					v.setZIndex(Renderer.hover.MIN_Z_INDEX + i);
				});
			}

			return Renderer.hover._getNextZIndex(hoverId);
		} else return out;
	}

	static _isIntersectRect (r1, r2) {
		return r1.left <= r2.right
			&& r2.left <= r1.right
			&& r1.top <= r2.bottom
			&& r2.top <= r1.bottom;
	}

	/**
	 * @param $content Content to append to the window.
	 * @param position The position of the window. Can be specified in various formats.
	 * @param [opts] Options object.
	 * @param [opts.isPermanent] If the window should have the expanded toolbar of a "permanent" window.
	 * @param [opts.title] The window title.
	 * @param [opts.isBookContent] If the hover window contains book content. Affects the styling of borders.
	 * @param [opts.pageUrl] A page URL which is navigable via a button in the window header
	 * @param [opts.cbClose] Callback to run on window close.
	 * @param [opts.width] An initial width for the window.
	 * @param [opts.height] An initial height fot the window.
	 * @param [opts.$pFnGetPopoutContent] A function which loads content for this window when it is popped out.
	 * @param [opts.fnGetPopoutSize] A function which gets a `{width: ..., height: ...}` object with dimensions for a
	 * popout window.
	 * @param [opts.isPopout] If the window should be immediately popped out.
	 * @param [opts.compactReferenceData] Reference (e.g. page/source/hash/others) which can be used to load the contents into the DM screen.
	 * @param [opts.sourceData] Source JSON (as raw as possible) used to construct this popout.
	 */
	static getShowWindow ($content, position, opts) {
		opts = opts || {};

		Renderer.hover._doInit();

		const initialWidth = opts.width == null ? Renderer.hover._DEFAULT_WIDTH_PX : opts.width;
		const initialZIndex = Renderer.hover._getNextZIndex();

		const $body = $(position.window.document.body);
		const $hov = $(`<div class="hwin"></div>`)
			.css({
				"right": -initialWidth,
				"width": initialWidth,
				"zIndex": initialZIndex,
			});
		const $wrpContent = $(`<div class="hwin__wrp-table"></div>`);
		if (opts.height != null) $wrpContent.css("height", opts.height);
		const $hovTitle = $(`<span class="window-title min-w-0 ve-overflow-ellipsis" title="${`${opts.title || ""}`.qq()}">${opts.title || ""}</span>`);

		const hoverWindow = {};
		const hoverId = Renderer.hover._getNextId();
		Renderer.hover._WINDOW_METAS[hoverId] = hoverWindow;
		const mouseUpId = `mouseup.${hoverId} touchend.${hoverId}`;
		const mouseMoveId = `mousemove.${hoverId} touchmove.${hoverId}`;
		const resizeId = `resize.${hoverId}`;
		const drag = {};

		const $brdrTopRightResize = $(`<div class="hoverborder__resize-ne"></div>`)
			.on("mousedown touchstart", (evt) => Renderer.hover._getShowWindow_handleDragMousedown({hoverWindow, hoverId, $hov, drag, $wrpContent}, {evt, type: 1}));

		const $brdrRightResize = $(`<div class="hoverborder__resize-e"></div>`)
			.on("mousedown touchstart", (evt) => Renderer.hover._getShowWindow_handleDragMousedown({hoverWindow, hoverId, $hov, drag, $wrpContent}, {evt, type: 2}));

		const $brdrBottomRightResize = $(`<div class="hoverborder__resize-se"></div>`)
			.on("mousedown touchstart", (evt) => Renderer.hover._getShowWindow_handleDragMousedown({hoverWindow, hoverId, $hov, drag, $wrpContent}, {evt, type: 3}));

		const $brdrBtm = $(`<div class="hoverborder hoverborder--btm ${opts.isBookContent ? "hoverborder-book" : ""}"><div class="hoverborder__resize-s"></div></div>`)
			.on("mousedown touchstart", (evt) => Renderer.hover._getShowWindow_handleDragMousedown({hoverWindow, hoverId, $hov, drag, $wrpContent}, {evt, type: 4}));

		const $brdrBtmLeftResize = $(`<div class="hoverborder__resize-sw"></div>`)
			.on("mousedown touchstart", (evt) => Renderer.hover._getShowWindow_handleDragMousedown({hoverWindow, hoverId, $hov, drag, $wrpContent}, {evt, type: 5}));

		const $brdrLeftResize = $(`<div class="hoverborder__resize-w"></div>`)
			.on("mousedown touchstart", (evt) => Renderer.hover._getShowWindow_handleDragMousedown({hoverWindow, hoverId, $hov, drag, $wrpContent}, {evt, type: 6}));

		const $brdrTopLeftResize = $(`<div class="hoverborder__resize-nw"></div>`)
			.on("mousedown touchstart", (evt) => Renderer.hover._getShowWindow_handleDragMousedown({hoverWindow, hoverId, $hov, drag, $wrpContent}, {evt, type: 7}));

		const $brdrTopResize = $(`<div class="hoverborder__resize-n"></div>`)
			.on("mousedown touchstart", (evt) => Renderer.hover._getShowWindow_handleDragMousedown({hoverWindow, hoverId, $hov, drag, $wrpContent}, {evt, type: 8}));

		const $brdrTop = $(`<div class="hoverborder hoverborder--top ${opts.isBookContent ? "hoverborder-book" : ""}" ${opts.isPermanent ? `data-perm="true"` : ""}></div>`)
			.on("mousedown touchstart", (evt) => Renderer.hover._getShowWindow_handleDragMousedown({hoverWindow, hoverId, $hov, drag, $wrpContent}, {evt, type: 9}))
			.on("contextmenu", (evt) => {
				Renderer.hover._contextMenuLastClicked = {
					hoverId,
				};
				ContextUtil.pOpenMenu(evt, Renderer.hover._contextMenu);
			});

		$(position.window.document)
			.on(mouseUpId, (evt) => {
				if (drag.type) {
					if (drag.type < 9) {
						$wrpContent.css("max-height", "");
						$hov.css("max-width", "");
					}
					Renderer.hover._getShowWindow_adjustPosition({$hov, $wrpContent, position});

					if (drag.type === 9) {
						// handle mobile button touches
						if (EventUtil.isUsingTouch() && evt.target.classList.contains("hwin__top-border-icon")) {
							evt.preventDefault();
							drag.type = 0;
							$(evt.target).click();
							return;
						}
					}
					drag.type = 0;
				}
			})
			.on(mouseMoveId, (evt) => {
				const args = {$wrpContent, $hov, drag, evt};
				switch (drag.type) {
					case 1: Renderer.hover._getShowWindow_handleNorthDrag(args); Renderer.hover._getShowWindow_handleEastDrag(args); break;
					case 2: Renderer.hover._getShowWindow_handleEastDrag(args); break;
					case 3: Renderer.hover._getShowWindow_handleSouthDrag(args); Renderer.hover._getShowWindow_handleEastDrag(args); break;
					case 4: Renderer.hover._getShowWindow_handleSouthDrag(args); break;
					case 5: Renderer.hover._getShowWindow_handleSouthDrag(args); Renderer.hover._getShowWindow_handleWestDrag(args); break;
					case 6: Renderer.hover._getShowWindow_handleWestDrag(args); break;
					case 7: Renderer.hover._getShowWindow_handleNorthDrag(args); Renderer.hover._getShowWindow_handleWestDrag(args); break;
					case 8: Renderer.hover._getShowWindow_handleNorthDrag(args); break;
					case 9: {
						const diffX = drag.startX - EventUtil.getClientX(evt);
						const diffY = drag.startY - EventUtil.getClientY(evt);
						$hov.css("left", drag.baseLeft - diffX)
							.css("top", drag.baseTop - diffY);
						drag.startX = EventUtil.getClientX(evt);
						drag.startY = EventUtil.getClientY(evt);
						drag.baseTop = parseFloat($hov.css("top"));
						drag.baseLeft = parseFloat($hov.css("left"));
						break;
					}
				}
			});
		$(position.window).on(resizeId, () => Renderer.hover._getShowWindow_adjustPosition({$hov, $wrpContent, position}));

		$brdrTop.attr("data-display-title", false);
		$brdrTop.on("dblclick", () => Renderer.hover._getShowWindow_doToggleMinimizedMaximized({$brdrTop, $hov}));
		$brdrTop.append($hovTitle);
		const $brdTopRhs = $(`<div class="ve-flex ml-auto no-shrink"></div>`).appendTo($brdrTop);

		if (opts.pageUrl && !position.window._IS_POPOUT && !Renderer.get().isInternalLinksDisabled()) {
			const $btnGotoPage = $(`<a class="hwin__top-border-icon glyphicon glyphicon-modal-window" title="Go to Page" href="${opts.pageUrl}"></a>`)
				.appendTo($brdTopRhs);
		}

		if (!position.window._IS_POPOUT && !opts.isPopout) {
			const $btnPopout = $(`<span class="hwin__top-border-icon glyphicon glyphicon-new-window hvr__popout" title="Open as Popup Window"></span>`)
				.on("click", evt => {
					evt.stopPropagation();
					return Renderer.hover._getShowWindow_pDoPopout({$hov, position, mouseUpId, mouseMoveId, resizeId, hoverId, opts, hoverWindow, $content}, {evt});
				})
				.appendTo($brdTopRhs);
		}

		if (opts.sourceData) {
			const btnPopout = e_({
				tag: "span",
				clazz: `hwin__top-border-icon hwin__top-border-icon--text`,
				title: "Show Source Data",
				text: "{}",
				click: evt => {
					evt.stopPropagation();
					evt.preventDefault();

					const $content = Renderer.hover.$getHoverContent_statsCode(opts.sourceData);
					Renderer.hover.getShowWindow(
						$content,
						Renderer.hover.getWindowPositionFromEvent(evt),
						{
							title: [opts.sourceData._displayName || opts.sourceData.name, "Source Data"].filter(Boolean).join(" \u2014 "),
							isPermanent: true,
							isBookContent: true,
						},
					);
				},
			});
			$brdTopRhs.append(btnPopout);
		}

		const $btnClose = $(`<span class="hwin__top-border-icon glyphicon glyphicon-remove" title="Close (CTRL to Close All)"></span>`)
			.on("click", (evt) => {
				evt.stopPropagation();

				if (EventUtil.isCtrlMetaKey(evt)) {
					Renderer.hover._doCloseAllWindows();
					return;
				}

				Renderer.hover._getShowWindow_doClose({$hov, position, mouseUpId, mouseMoveId, resizeId, hoverId, opts, hoverWindow});
			}).appendTo($brdTopRhs);

		$wrpContent.append($content);

		$hov.append($brdrTopResize).append($brdrTopRightResize).append($brdrRightResize).append($brdrBottomRightResize)
			.append($brdrBtmLeftResize).append($brdrLeftResize).append($brdrTopLeftResize)

			.append($brdrTop)
			.append($wrpContent)
			.append($brdrBtm);

		$body.append($hov);

		Renderer.hover._getShowWindow_setPosition({$hov, $wrpContent, position}, position);

		hoverWindow.$windowTitle = $hovTitle;
		hoverWindow.zIndex = initialZIndex;
		hoverWindow.setZIndex = Renderer.hover._getNextZIndex.bind(this, {$hov, hoverWindow});

		hoverWindow.setPosition = Renderer.hover._getShowWindow_setPosition.bind(this, {$hov, $wrpContent, position});
		hoverWindow.setIsPermanent = Renderer.hover._getShowWindow_setIsPermanent.bind(this, {opts, $brdrTop});
		hoverWindow.doClose = Renderer.hover._getShowWindow_doClose.bind(this, {$hov, position, mouseUpId, mouseMoveId, resizeId, hoverId, opts, hoverWindow});
		hoverWindow.doMaximize = Renderer.hover._getShowWindow_doMaximize.bind(this, {$brdrTop, $hov});
		hoverWindow.doZIndexToFront = Renderer.hover._getShowWindow_doZIndexToFront.bind(this, {$hov, hoverWindow, hoverId});

		hoverWindow.getPosition = Renderer.hover._getShowWindow_getPosition.bind(this, {$hov, $wrpContent, position});

		hoverWindow.$setContent = ($contentNxt) => $wrpContent.empty().append($contentNxt);

		if (opts.isPopout) Renderer.hover._getShowWindow_pDoPopout({$hov, position, mouseUpId, mouseMoveId, resizeId, hoverId, opts, hoverWindow, $content});

		return hoverWindow;
	}

	static _getShowWindow_doClose ({$hov, position, mouseUpId, mouseMoveId, resizeId, hoverId, opts, hoverWindow}) {
		$hov.remove();
		$(position.window.document).off(mouseUpId);
		$(position.window.document).off(mouseMoveId);
		$(position.window).off(resizeId);

		delete Renderer.hover._WINDOW_METAS[hoverId];

		if (opts.cbClose) opts.cbClose(hoverWindow);
	}

	static _getShowWindow_handleDragMousedown ({hoverWindow, hoverId, $hov, drag, $wrpContent}, {evt, type}) {
		if (evt.which === 0 || evt.which === 1) evt.preventDefault();
		hoverWindow.zIndex = Renderer.hover._getNextZIndex(hoverId);
		$hov.css({
			"z-index": hoverWindow.zIndex,
			"animation": "initial",
		});
		drag.type = type;
		drag.startX = EventUtil.getClientX(evt);
		drag.startY = EventUtil.getClientY(evt);
		drag.baseTop = parseFloat($hov.css("top"));
		drag.baseLeft = parseFloat($hov.css("left"));
		drag.baseHeight = $wrpContent.height();
		drag.baseWidth = parseFloat($hov.css("width"));
		if (type < 9) {
			$wrpContent.css({
				"height": drag.baseHeight,
				"max-height": "initial",
			});
			$hov.css("max-width", "initial");
		}
	}

	static _getShowWindow_isOverHoverTarget ({evt, target}) {
		return EventUtil.getClientX(evt) >= target.left
			&& EventUtil.getClientX(evt) <= target.left + target.width
			&& EventUtil.getClientY(evt) >= target.top
			&& EventUtil.getClientY(evt) <= target.top + target.height;
	}

	static _getShowWindow_handleNorthDrag ({$wrpContent, $hov, drag, evt}) {
		const diffY = Math.max(drag.startY - EventUtil.getClientY(evt), 80 - drag.baseHeight); // prevent <80 height, as this will cause the box to move downwards
		$wrpContent.css("height", drag.baseHeight + diffY);
		$hov.css("top", drag.baseTop - diffY);
		drag.startY = EventUtil.getClientY(evt);
		drag.baseHeight = $wrpContent.height();
		drag.baseTop = parseFloat($hov.css("top"));
	}

	static _getShowWindow_handleEastDrag ({$wrpContent, $hov, drag, evt}) {
		const diffX = drag.startX - EventUtil.getClientX(evt);
		$hov.css("width", drag.baseWidth - diffX);
		drag.startX = EventUtil.getClientX(evt);
		drag.baseWidth = parseFloat($hov.css("width"));
	}

	static _getShowWindow_handleSouthDrag ({$wrpContent, $hov, drag, evt}) {
		const diffY = drag.startY - EventUtil.getClientY(evt);
		$wrpContent.css("height", drag.baseHeight - diffY);
		drag.startY = EventUtil.getClientY(evt);
		drag.baseHeight = $wrpContent.height();
	}

	static _getShowWindow_handleWestDrag ({$wrpContent, $hov, drag, evt}) {
		const diffX = Math.max(drag.startX - EventUtil.getClientX(evt), 150 - drag.baseWidth);
		$hov.css("width", drag.baseWidth + diffX)
			.css("left", drag.baseLeft - diffX);
		drag.startX = EventUtil.getClientX(evt);
		drag.baseWidth = parseFloat($hov.css("width"));
		drag.baseLeft = parseFloat($hov.css("left"));
	}

	static _getShowWindow_doToggleMinimizedMaximized ({$brdrTop, $hov}) {
		const curState = $brdrTop.attr("data-display-title");
		const isNextMinified = curState === "false";
		$brdrTop.attr("data-display-title", isNextMinified);
		$brdrTop.attr("data-perm", true);
		$hov.toggleClass("hwin--minified", isNextMinified);
	}

	static _getShowWindow_doMaximize ({$brdrTop, $hov}) {
		$brdrTop.attr("data-display-title", false);
		$hov.toggleClass("hwin--minified", false);
	}

	static async _getShowWindow_pDoPopout ({$hov, position, mouseUpId, mouseMoveId, resizeId, hoverId, opts, hoverWindow, $content}, {evt} = {}) {
		const dimensions = opts.fnGetPopoutSize ? opts.fnGetPopoutSize() : {width: 600, height: $content.height()};
		const win = window.open(
			"",
			opts.title || "",
			`width=${dimensions.width},height=${dimensions.height}location=0,menubar=0,status=0,titlebar=0,toolbar=0`,
		);

		// If this is a new window, bootstrap general page elements/variables.
		// Otherwise, we can skip straight to using the window.
		if (!win._IS_POPOUT) {
			win._IS_POPOUT = true;
			win.document.write(`
				<!DOCTYPE html>
				<html lang="en" class="ve-popwindow ${typeof styleSwitcher !== "undefined" ? styleSwitcher.getDayNightClassNames() : ""}"><head>
					<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
					<title>${opts.title}</title>
					${$(`link[rel="stylesheet"][href]`).map((i, e) => e.outerHTML).get().join("\n")}
					<style>
						html, body { width: 100%; height: 100%; }
						body { overflow-y: scroll; }
						.hwin--popout { max-width: 100%; max-height: 100%; box-shadow: initial; width: 100%; overflow-y: auto; }
					</style>
				</head><body class="rd__body-popout">
				<div class="hwin hoverbox--popout hwin--popout"></div>
				<script type="text/javascript" src="js/parser.js"></script>
				<script type="text/javascript" src="js/utils.js"></script>
				<script type="text/javascript" src="lib/jquery.js"></script>
				</body></html>
			`);

			win.Renderer = Renderer;

			let ticks = 50;
			while (!win.document.body && ticks-- > 0) await MiscUtil.pDelay(5);

			win.$wrpHoverContent = $(win.document).find(`.hoverbox--popout`);
		}

		let $cpyContent;
		if (opts.$pFnGetPopoutContent) {
			$cpyContent = await opts.$pFnGetPopoutContent();
		} else {
			$cpyContent = $content.clone(true, true);
		}

		$cpyContent.appendTo(win.$wrpHoverContent.empty());

		Renderer.hover._getShowWindow_doClose({$hov, position, mouseUpId, mouseMoveId, resizeId, hoverId, opts, hoverWindow});
	}

	static _getShowWindow_setPosition ({$hov, $wrpContent, position}, positionNxt) {
		switch (positionNxt.mode) {
			case "autoFromElement": {
				const bcr = $hov[0].getBoundingClientRect();

				if (positionNxt.isFromBottom) $hov.css("top", positionNxt.bcr.top - (bcr.height + 10));
				else $hov.css("top", positionNxt.bcr.top + positionNxt.bcr.height + 10);

				if (positionNxt.isFromRight) $hov.css("left", (positionNxt.clientX || positionNxt.bcr.left) - (bcr.width + 10));
				else $hov.css("left", (positionNxt.clientX || (positionNxt.bcr.left + positionNxt.bcr.width)) + 10);

				// region Sync position info when updating
				if (position !== positionNxt) {
					Renderer.hover._WINDOW_POSITION_PROPS_FROM_EVENT
						.forEach(prop => {
							position[prop] = positionNxt[prop];
						});
				}
				// endregion

				break;
			}
			case "exact": {
				$hov.css({
					"left": positionNxt.x,
					"top": positionNxt.y,
				});
				break;
			}
			case "exactVisibleBottom": {
				$hov.css({
					"left": positionNxt.x,
					"top": positionNxt.y,
					"animation": "initial", // Briefly remove the animation so we can calculate the height
				});

				let yPos = positionNxt.y;

				const {bottom: posBottom, height: winHeight} = $hov[0].getBoundingClientRect();
				const height = position.window.innerHeight;
				if (posBottom > height) {
					yPos = position.window.innerHeight - winHeight;
					$hov.css({
						"top": yPos,
						"animation": "",
					});
				}

				break;
			}
			default: throw new Error(`Positiong mode unimplemented: "${positionNxt.mode}"`);
		}

		Renderer.hover._getShowWindow_adjustPosition({$hov, $wrpContent, position});
	}

	static _getShowWindow_adjustPosition ({$hov, $wrpContent, position}) {
		const eleHov = $hov[0];
		const wrpContent = $wrpContent[0];

		const bcr = eleHov.getBoundingClientRect().toJSON();
		const screenHeight = position.window.innerHeight;
		const screenWidth = position.window.innerWidth;

		// readjust position...
		// ...if vertically clipping off screen
		if (bcr.top < 0) {
			bcr.top = 0;
			bcr.bottom = bcr.top + bcr.height;
			eleHov.style.top = `${bcr.top}px`;
		} else if (bcr.top >= screenHeight - Renderer.hover._BAR_HEIGHT) {
			bcr.top = screenHeight - Renderer.hover._BAR_HEIGHT;
			bcr.bottom = bcr.top + bcr.height;
			eleHov.style.top = `${bcr.top}px`;
		}

		// ...if horizontally clipping off screen
		if (bcr.left < 0) {
			bcr.left = 0;
			bcr.right = bcr.left + bcr.width;
			eleHov.style.left = `${bcr.left}px`;
		} else if (bcr.left + bcr.width + Renderer.hover._BODY_SCROLLER_WIDTH_PX > screenWidth) {
			bcr.left = Math.max(screenWidth - bcr.width - Renderer.hover._BODY_SCROLLER_WIDTH_PX, 0);
			bcr.right = bcr.left + bcr.width;
			eleHov.style.left = `${bcr.left}px`;
		}

		// Prevent window "flickering" when hovering a link
		if (
			position.isPreventFlicker
			&& Renderer.hover._isIntersectRect(bcr, position.bcr)
		) {
			if (position.isFromBottom) {
				bcr.height = position.bcr.top - 5;
				wrpContent.style.height = `${bcr.height}px`;
			} else {
				bcr.height = screenHeight - position.bcr.bottom - 5;
				wrpContent.style.height = `${bcr.height}px`;
			}
		}
	}

	static _getShowWindow_getPosition ({$hov, $wrpContent}) {
		return {
			wWrpContent: $wrpContent.width(),
			hWrapContent: $wrpContent.height(),
		};
	}

	static _getShowWindow_setIsPermanent ({opts, $brdrTop}, isPermanent) {
		opts.isPermanent = isPermanent;
		$brdrTop.attr("data-perm", isPermanent);
	}

	static _getShowWindow_setZIndex ({$hov, hoverWindow}, zIndex) {
		$hov.css("z-index", zIndex);
		hoverWindow.zIndex = zIndex;
	}

	static _getShowWindow_doZIndexToFront ({$hov, hoverWindow, hoverId}) {
		const nxtZIndex = Renderer.hover._getNextZIndex(hoverId);
		Renderer.hover._getShowWindow_setZIndex({$hov, hoverWindow}, nxtZIndex);
	}

	static getInlineHover (entry, opts) {
		return {
			// Re-use link handlers, as the inline version is a simplified version
			html: `onmouseover="Renderer.hover.handleInlineMouseOver(event, this)" onmouseleave="Renderer.hover.handleLinkMouseLeave(event, this)" onmousemove="Renderer.hover.handleLinkMouseMove(event, this)" data-vet-entry="${JSON.stringify(entry).qq()}" ${opts ? `data-vet-opts="${JSON.stringify(opts).qq()}"` : ""} ${Renderer.hover.getPreventTouchString()}`,
		};
	}

	static getPreventTouchString () {
		return `ontouchstart="Renderer.hover.handleTouchStart(event, this)"`;
	}

	// region entry fetching
	static getEntityLink (
		ent,
		{
			displayText = null,
			prop = null,
			isLowerCase = false,
			isTitleCase = false,
		} = {},
	) {
		if (isLowerCase && isTitleCase) throw new Error(`"isLowerCase" and "isTitleCase" are mutually exclusive!`);

		const name = isLowerCase ? ent.name.toLowerCase() : isTitleCase ? ent.name.toTitleCase() : ent.name;
		let parts;
		if (UrlUtil.PAGE_TO_PROPS[UrlUtil.PG_SONG].includes(prop || ent.__prop)) {
			 parts = [
				 ent.id,
				 ent.source,
				 displayText || ent._fullName || ent.name,
			]
		} else {
			parts = [
				name,
				ent.source,
				displayText || "",
			];
		}

		while (parts.length && !parts.last()?.length) parts.pop();

		return Renderer.get().render(`{@${Parser.getPropTag(prop || ent.__prop)} ${parts.join("|")}}`);
	}

	static getRefMetaFromTag (str) {
		// convert e.g. `"{#itemEntry Ring of Resistance|DMG}"`
		//   to `{type: "refItemEntry", "itemEntry": "Ring of Resistance|DMG"}`
		str = str.slice(2, -1);
		const [tag, ...refParts] = str.split(" ");
		const ref = refParts.join(" ");
		const type = `ref${tag.uppercaseFirst()}`;
		return {type, [tag]: ref};
	}
	// endregion

	static getGenericCompactRenderedString (entry, depth = 0) {
		return `
			<tr class="text homebrew-hover"><td colspan="6">
			${Renderer.get().setFirstSection(true).render(entry, depth)}
			</td></tr>
		`;
	}

	static getFnRenderCompact (page, {isStatic = false} = {}) {
		switch (page) {
			case "generic":
			case "hover": return Renderer.hover.getGenericCompactRenderedString;
			case UrlUtil.PG_SONG: return Renderer.song.getCompactRenderedString;
			default:
				if (Renderer[page]?.getCompactRenderedString) return Renderer[page].getCompactRenderedString;
				return null;
		}
	}

	static isSmallScreen (evt) {
		if (typeof window === "undefined") return false;

		evt = evt || {};
		const win = (evt.view || {}).window || window;
		return win.innerWidth <= 768;
	}

	/**
	 * @param page
	 * @param toRender
	 * @param [opts]
	 * @param [opts.isBookContent]
	 * @param [opts.isStatic] If this content is to be "static," i.e. display only, containing minimal interactive UI.
	 * @param [opts.fnRender]
	 * @param [renderFnOpts]
	 */
	static $getHoverContent_stats (page, toRender, opts, renderFnOpts) {
		opts = opts || {};
		const fnRender = opts.fnRender || Renderer.hover.getFnRenderCompact(page, {isStatic: opts.isStatic});
		return $$`<table class="w-100 stats ${opts.isBookContent ? `stats--book` : ""}">${fnRender(toRender, renderFnOpts)}</table>`;
	}

	static $getHoverContent_statsCode (toRender, {isSkipClean = false, title = null} = {}) {
		const cleanCopy = isSkipClean ? toRender : DataUtil.cleanJson(MiscUtil.copyFast(toRender));
		return Renderer.hover.$getHoverContent_miscCode(
			title || [cleanCopy.name, "Source Data"].filter(Boolean).join(" \u2014 "),
			JSON.stringify(cleanCopy, null, "\t"),
		);
	}

	static $getHoverContent_miscCode (name, code) {
		const toRenderCode = {
			type: "code",
			name,
			preformatted: code,
		};
		return $$`<table class="w-100 stats stats--book">${Renderer.get().render(toRenderCode)}</table>`;
	}

	/**
	 * @param toRender
	 * @param [opts]
	 * @param [opts.isBookContent]
	 * @param [opts.isLargeBookContent]
	 * @param [opts.depth]
	 */
	static $getHoverContent_generic (toRender, opts) {
		opts = opts || {};

		return $$`<table class="w-100 stats ${opts.isBookContent || opts.isLargeBookContent ? "stats--book" : ""} ${opts.isLargeBookContent ? "stats--book-large" : ""}">${Renderer.hover.getGenericCompactRenderedString(toRender, opts.depth || 0)}</table>`;
	}

	/**
	 * @param evt
	 * @param entity
	 */
	static doPopoutCurPage (evt, entity) {
		const page = UrlUtil.getCurrentPage();
		const $content = Renderer.hover.$getHoverContent_stats(page, entity);
		Renderer.hover.getShowWindow(
			$content,
			Renderer.hover.getWindowPositionFromEvent(evt),
			{
				pageUrl: `#${UrlUtil.autoEncodeHash(entity)}`,
				title: entity._displayName || entity.name,
				isPermanent: true,
				sourceData: entity,
				width: Renderer.hover._getDefaultWidth(entity)
			},
		);
	}
};

// dig down until we find a name, as feature names can be nested
Renderer.findName = function (entry) { return CollectionUtil.dfs(entry, {prop: "name"}); };
Renderer.findSource = function (entry) { return CollectionUtil.dfs(entry, {prop: "source"}); };
Renderer.findEntry = function (entry) { return CollectionUtil.dfs(entry, {fnMatch: obj => obj.name && obj?.entries?.length}); };

/**
 * @param {string} str
 * @param {?Set<string>} allowlistTags
 * @param {?Set<string>} blocklistTags
 */
Renderer.stripTags = function (str, {allowlistTags = null, blocklistTags = null} = {}) {
	if (!str) return str;

	const ptrAccum = {_: ""};
	Renderer._stripTags_textRender({str, ptrAccum, allowlistTags, blocklistTags});
	return ptrAccum._;
};

Renderer._stripTags_textRender = function ({str, ptrAccum, allowlistTags = null, blocklistTags = null} = {}) {
	const tagSplit = Renderer.splitByTags(str);
	const len = tagSplit.length;
	for (let i = 0; i < len; ++i) {
		const s = tagSplit[i];
		if (!s) continue;

		if (!s.startsWith("{@")) {
			ptrAccum._ += s;
			continue;
		}

		const [tag, text] = Renderer.splitFirstSpace(s.slice(1, -1));

		if (
			(allowlistTags != null && allowlistTags.has(tag))
			|| (blocklistTags != null && !blocklistTags.has(tag))
		) {
			ptrAccum._ += s;
			continue;
		}

		const tagInfo = Renderer.tag.TAG_LOOKUP[tag];
		if (!tagInfo) throw new Error(`Unhandled tag: "${tag}"`);
		const stripped = tagInfo.getStripped(tag, text);

		Renderer._stripTags_textRender({str: stripped, ptrAccum, allowlistTags, blocklistTags});
	}
};

Renderer.HEAD_NEG_1 = "rd__b--0";
Renderer.HEAD_0 = "rd__b--1";
Renderer.HEAD_1 = "rd__b--2";
Renderer.HEAD_2 = "rd__b--3";
Renderer.HEAD_2_SUB_VARIANT = "rd__b--4";
Renderer.DATA_NONE = "data-none";
