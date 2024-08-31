const CONTROLLER = new AbortController();

function fetch_json_options(method, data) {
  return {
    body: JSON.stringify(data),
    method: method,
    headers: {
      "Content-Type": "application/json",
    },
    signal: CONTROLLER.signal,
  }
}

function fetch_json_missing(type, id) {
  const item = {
    id: id,
    type: type,
  }
  const missing_options = fetch_json_options("PUT", item);
  return fetch("/missing", missing_options);
}

function empty_json_promise() {
  return new Promise(resolve => resolve(undefined));
  // return new Promise(resolve => resolve({}));
}

class FetchCache {
  constructor() {
    this.id = Date.now();
    this.CACHES = {
      class_set: {},
      icon: {},
      item: {},
      enchant: {},
    };
  }
  async fetch_item_data(id) {
    return this._fetch_wrap("item", id);
  }
  async fetch_enchant_data(id) {
    return this._fetch_wrap("enchant", id);
  }
  async fetch_class_set(class_name) {
    class_name = class_name.toLowerCase().replace(" ", "");
    if (!this.CACHES.class_set[class_name]) {
      await this._fetch_class_set(class_name);
    }
    return this.CACHES.class_set[class_name];
  }
  async icon_exists(id) {
    const cache = this.CACHES.icon;
    if (!cache[id]) {
      cache[id] = this._fetch_icon_exists(id);
    }
    return cache[id];
  }

  async _fetch_json(type, id) {
    const url = `/static/${type}/${id}.json`;
    const cache_options = {signal: CONTROLLER.signal};
    const cache_response = await fetch(url, cache_options);
    if (cache_response.status == 200) {
      return cache_response.json();
    }
  }
  async _fetch_missing_check_exists(type, id) {
    const missing_response = await fetch_json_missing(type, id);
    return [200, 201, 409].includes(missing_response.status);
  }
  async _fetch_json_wrap(type, id) {
    const fetch_try_1 = await this._fetch_json(type, id);
    if (fetch_try_1) return fetch_try_1;

    const missing_created = await this._fetch_missing_check_exists(type, id);
    if (missing_created) {
      const fetch_try_2 = await this._fetch_json(type, id);
      if (fetch_try_2) return fetch_try_2;
    } 

    return empty_json_promise();
  }
  async _fetch_wrap(type, id) {
    const cache = this.CACHES[type];
    if (!cache[id]) {
      cache[id] = this._fetch_json_wrap(type, id);
    }
    return cache[id];
  }
  async _fetch_class_set(class_name) {
    const response = await fetch(`/static/sets/${class_name}.json`);
    this.CACHES.class_set[class_name] = response.json();
  }
  async _fetch_icon_exists(id) {
    const fetch_try_1 = await fetch(`/static/icons/${id}.jpg`);
    if (fetch_try_1.status != 404) return true;

    return await this._fetch_missing_check_exists("icon", id);
  }
}

export const CACHE = new FetchCache();
