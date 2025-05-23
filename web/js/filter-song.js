"use strict";
class PageFilterSong extends PageFilter {
	constructor () {
		super({
			sourceFilterOpts: {
				selFn: v => SourceUtil.getFilterGroup(v) === SourceUtil.FILTER_GROUP_HOMEBREW || SourceUtil.isEn(v),
			},
		});

		this._factionFilter = new Filter({
			header: "Faction",
			displayFn: Parser.renderFaction,
		});

		this._typeFilter = new Filter({
			header: "Type",
			items: ["attachment", "unit", "ncu", "tactics", "special"],
			itemSortFn: null,
			displayFn: Parser.renderProp,
		});

		this._characterFilter = new Filter({
			header: "Character/Commander",
			items: ["Is a Character", "Is a Commander"]
		});

		this._versionFilter = new Filter({
			header: "Version"
		});

		this._trayFilter = new Filter({
			header: "Tray",
			displayFn: t => t.uppercaseFirst()
		});

		this._costFilter = new Filter({
			header: "Cost",
			displayFnMini: c => `Cost: ${c}`
		});

		this._speedFilter = new Filter({
			header: "Speed",
			displayFnMini: s => `Speed: ${s}`
		});

		this._defenseFilter = new Filter({
			header: "Defense",
			displayFnMini: d => `Defense: ${d}+`,
			displayFn: d => d + "+",
		});

		this._moraleFilter = new Filter({
			header: "Morale",
			displayFnMini: m => `Morale: ${m}+`,
			displayFn: m => m + "+"
		});

		this._abilitiesFilter = new SearchableFilter({
			header: "Abilities"
		});

		this._toHitFilter = new Filter({
			header: "To Hit",
			displayFnMini: h => `Hit: ${h}`,
		});
		this._attackDiceFilter = new Filter({
			header: "Attack Dice",
			itemSortFn: (a, b) => {
				if (typeof FilterItem !== "undefined") {
					if (a instanceof FilterItem) a = a.item;
					if (b instanceof FilterItem) b = b.item;
				}
				return b.split("/").length - a.split("/").length || SortUtil.ascSort(b, a);
			}
		});
		this._attackTypeFilter = new Filter({
			header: "Attack Type",
			items: ["Melee", "Short Range", "Long Range"],
			itemSortFn: null,
		});
		this._attackFilter = new MultiFilter({
			header: "Attacks",
			filters: [this._attackTypeFilter, this._attackDiceFilter, this._toHitFilter]
		})

		this._tacticsFilter = new Filter({
			header: "Card Type",
			items: ["Basedeck", "Commander Card"]
		});
		this._commanderFilter = new SearchableFilter({
			header: "Commander",
		});
		this._tacticsMultiFilter = new MultiFilter({
			header: "Tactic Cards",
			filters: [this._tacticsFilter, this._commanderFilter],
		});
	}

	static mutateForFilters (e) {
		e._fToHit = (e.attacks || []).map(a => a.hit + "+");
		e._fAttackDice = (e.attacks || []).map(a => a.dice.join("/"));
		e._fAttackTypes = (e.attacks || []).map(a => a.type === "melee" ? "Melee" : a.type.uppercaseFirst() + " Range");
		e._fAbilities = (e.abilities || []).map(a => typeof a === "string" ? a : a.name).filter(Boolean).map(s => s.toTitleCase());
		e._fCharacter = [];
		if (e.commander === true) e._fCharacter.push("Is a Commander", "Is a Character");
		else if (e.character || (e.__prop === "unit" && e.title)) e._fCharacter.push("Is a Character");

		e._fTactics = [];
		if (e.__prop === "tactics" && e.commander) {
			e._fCommander = e.commander.title ? `${e.commander.name}, ${e.commander.title}` : e.commander.name;
			e._fTactics.push("Commander Card");
		}
		else if (e.__prop === "tactics") e._fTactics.push("Basedeck");
	}

	addToFilters (e, isExcluded) {
		this._sourceFilter.addItem(e.lang);
		this._factionFilter.addItem(e.faction);
		this._versionFilter.addItem(e.version);
		this._trayFilter.addItem(e.tray);
		if (e.cost !== undefined) this._costFilter.addItem(String(e.cost));
		if (e.speed !== undefined) this._speedFilter.addItem(String(e.speed));
		if (e.defense !== undefined) this._defenseFilter.addItem(String(e.defense));
		if (e.morale !== undefined) this._moraleFilter.addItem(String(e.morale));
		this._attackTypeFilter.addItem(e._fAttackTypes);
		this._toHitFilter.addItem(e._fToHit);
		this._attackDiceFilter.addItem(e._fAttackDice);
		this._abilitiesFilter.addItem(e._fAbilities);
		this._characterFilter.addItem(e._fCharacter);
		this._tacticsFilter.addItem(e._fTactics);
		this._commanderFilter.addItem(e._fCommander);
	}

	async _pPopulateBoxOptions (opts) {
		opts.filters = [
			this._sourceFilter,
			this._versionFilter,
			this._typeFilter,
			this._characterFilter,
			this._trayFilter,
			this._factionFilter,
			this._costFilter,
			this._speedFilter,
			this._defenseFilter,
			this._moraleFilter,
			this._attackFilter,
			this._abilitiesFilter,
			this._tacticsMultiFilter,
		];
	}

	toDisplay (values, e) {
		return this._filterBox.toDisplay(
			values,
			e.source,
			e.version,
			e.__prop,
			e._fCharacter,
			e.tray,
			e.faction,
			e.cost,
			e.speed,
			e.defense,
			e.morale,
			[
				e._fAttackTypes,
				e._fAttackDice,
				e._fToHit,
			],
			e._fAbilities,
			[
				e._fTactics,
				e._fCommander,
			],
		);
	}
}

globalThis.PageFilterSong = PageFilterSong;

class ListSyntaxSong extends ListUiUtil.ListSyntax {
	build() {
		return {
			trigger: {
				help: `"trigger:<text>" ("/trigger/" for regex) to search within triggers.`,
				fn: (listItem, searchTerm) => {
					if (listItem.data._textCacheTrigger == null) listItem.data._textCacheTrigger = this._getSearchCacheTrigger(this._dataList[listItem.ix]);
					return this._listSyntax_isTextMatch(listItem.data._textCacheTrigger, searchTerm);
				},
			},
			text: {
				help: `"text:<text>" ("/text/" for regex) to search within ability text.`,
				fn: (listItem, searchTerm) => {
					if (listItem.data._textCacheText == null) listItem.data._textCacheText = this._getSearchCacheText(this._dataList[listItem.ix]);
					return this._listSyntax_isTextMatch(listItem.data._textCacheText, searchTerm);
				},
			},
		};
	}

	_getSearchCacheTrigger(entity) {
		let out = "";
		if (entity.__prop === "tactics") {
			out = entity.text.map(e => e.trigger).filter(Boolean).join(" -- ");
		} else if (["attachment", "unit"].includes(entity.__prop)) {
			out = entity.abilities.map(a => a.trigger).filter(Boolean).join(" -- ");
		}
		return out.replace(/[•*]/g, "").toLowerCase();
	}

	_getSearchCacheText(entity) {
		let out = "";
		if (entity.__prop === "tactics") {
			out = entity.text.map(e => (e.effect || []).join(" ")).join(" -- ");
		} else if (["ncu", "attachment", "unit"].includes(entity.__prop)) {
			out = entity.abilities.map(a => (a.effect || []).join(" ")).join(" -- ");
		}
		return out.replace(/[•*]/g, "").toLowerCase();
	}
}
globalThis.ListSyntaxSong = ListSyntaxSong;
