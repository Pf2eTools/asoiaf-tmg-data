"use strict";

class UtilsTableview {
	static _State = class {
		constructor () {
			this.rows = [];
			this.metasCbs = [];
		}
	};

	static show ({title, entities, colTransforms, sorter}) {
		const {$modal} = UiUtil.getShowModal({
			isWidth100: true,
			isHeight100: true,
			isUncappedWidth: true,
			isUncappedHeight: true,
			isEmpty: true,
		});

		const state = new UtilsTableview._State();

		state.metasCbs = Object.values(colTransforms)
			.map((c, i) => {
				const $cb = $(`<input type="checkbox" class="mr-2" checked>`)
					.click(() => {
						const $eles = $modal.find(`[data-col="${i}"]`);
						$eles.toggleVe($cb.prop("checked"));
					});

				const $wrp = $$`<label class="px-2 py-1 no-wrap ve-flex-inline-v-center">
					${$cb}
					<span>${c.name}</span>
				</label>`;

				return {$wrp, $cb, name: c.name};
			});

		const $btnCsv = $(`<button class="btn btn-primary">Download CSV</button>`).click(() => {
			DataUtil.userDownloadText(`${title}.csv`, this._getAsCsv({state}));
		});

		const $btnCopy = $(`<button class="btn btn-primary">Copy CSV to Clipboard</button>`).click(async () => {
			await MiscUtil.pCopyTextToClipboard(this._getAsCsv({state}));
			JqueryUtil.showCopiedEffect($btnCopy);
		});

		$$($modal)`<div class="split-v-center my-3">
			<div class="ve-flex-v-center ve-flex-wrap">${state.metasCbs.map(({$wrp}) => $wrp)}</div>
			<div class="btn-group no-shrink ve-flex-v-center ml-3">
				${$btnCsv}
				${$btnCopy}
			</div>
		</div>
		<hr class="hr-1">`;

		const tableHtml = this._getTableHtml({state, entities, colTransforms, sorter});
		$modal.append(tableHtml);
	}

	static _getAsCsv ({state}) {
		const headersActive = state.metasCbs.map(({$cb, name}, i) => {
			if (!$cb.prop("checked")) return null;
			return {name, ix: i};
		}).filter(Boolean);
		const parser = new DOMParser();
		const rows = state.rows.map(row => headersActive.map(({ix}) => parser.parseFromString(`<div>${row[ix]}</div>`, "text/html").documentElement.textContent));
		return DataUtil.getCsv(headersActive.map(({name}) => name), rows);
	}

	static _getTableHtml ({state, entities, colTransforms, sorter}) {
		let stack = `<div class="ve-overflow-y-auto w-100 h-100 ve-flex-col ve-overflow-x-auto">
			<table class="w-100 table-striped stats stats--book stats--book-large min-w-100 w-initial">
				<thead>
					<tr>${Object.values(colTransforms).map((c, i) => `<th data-col="${i}" class="px-2" colspan="${c.flex || 1}">${c.name}</th>`).join("")}</tr>
				</thead>
				<tbody>`;

		const listCopy = [...entities];
		if (sorter) listCopy.sort(sorter);
		listCopy.forEach(it => {
			stack += `<tr class="tview__row">`;
			const row = [];
			stack += Object.keys(colTransforms).map((k, i) => {
				const c = colTransforms[k];
				const val = c.transform == null ? it[k] : c.transform(k[0] === "_" ? it : it[k]);
				row.push(val);
				return `<td data-col="${i}" class="px-2" colspan="${c.flex || 1}">${val || ""}</td>`;
			}).join("");
			state.rows.push(row);
			stack += `</tr>`;
		});

		stack += `</tbody>
			</table>
		</div>`;

		return stack;
	}

	// region Default/generic transforms
	static COL_TRANSFORM_NAME = {name: "Name"};
	static COL_TRANSFORM_SOURCE = {name: "Source", transform: (it) => `<span class="${Parser.sourceJsonToColor(it)}" title="${Parser.sourceJsonToFull(it)}" ${Parser.sourceJsonToStyle(it)}>${Parser.sourceJsonToAbv(it)}</span>`};
	static COL_TRANSFORM_PAGE = {name: "Page"};
	// endregion
}
