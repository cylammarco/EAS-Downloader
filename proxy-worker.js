const ALLOWED_ORIGINS = new Set([
  "https://cylammarco.github.io",
]);

function isAllowedOrigin(origin) {
  if (ALLOWED_ORIGINS.has(origin)) {
    return true;
  }

  try {
    const url = new URL(origin);
    return url.protocol === "http:" && ["localhost", "127.0.0.1", "::1", "[::1]"].includes(url.hostname);
  } catch (_error) {
    return false;
  }
}

const EAS_REST_NODE_HOST_RE = /^eas-dps-rest-ops-node\d+\.esac\.esa\.int$/i;
const ALLOWED_HOSTS = new Set([
  "eas-dps-rest-ops.esac.esa.int",
  "eas-dps-cus-ops.esac.esa.int",
  "euclidsoc.esac.esa.int",
]);
const DSS_HOST = "euclidsoc.esac.esa.int";
const CUS_HOST = "eas-dps-cus-ops.esac.esa.int";
const MAX_OBJECTS_PER_PROXY_CHUNK = 20;
const OBJECT_FETCH_CONCURRENCY = 5;
const ALLOWED_PROJECTS = new Set(["TEST", "EUCLID", "ALL"]);

function corsHeaders(request) {
  const origin = request.headers.get("Origin");
  if (!origin || !isAllowedOrigin(origin)) {
    return {};
  }

  return {
    "Access-Control-Allow-Origin": origin,
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Vary": "Origin",
  };
}

function jsonError(request, status, message) {
  return new Response(message, {
    status,
    headers: {
      "Content-Type": "text/plain; charset=UTF-8",
      ...corsHeaders(request),
    },
  });
}

function jsonResponse(request, status, payload) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: {
      "Content-Type": "application/json; charset=UTF-8",
      ...corsHeaders(request),
    },
  });
}

function normalizeBasicAuth(value) {
  const rawValue = String(value || "").trim();
  const encodedValue = rawValue.replace(/^Basic\s+/i, "");
  if (!/^[A-Za-z0-9+/]+={0,2}$/.test(encodedValue) || encodedValue.length % 4 === 1) {
    return null;
  }

  try {
    atob(encodedValue);
  } catch (_error) {
    return null;
  }
  return `Basic ${encodedValue}`;
}

function isAllowedTarget(target) {
  return target.protocol === "https:" && (ALLOWED_HOSTS.has(target.hostname) || EAS_REST_NODE_HOST_RE.test(target.hostname));
}

function safeResponseHeaders(upstream, request) {
  const headers = new Headers(upstream.headers);
  headers.delete("set-cookie");
  headers.delete("www-authenticate");
  Object.entries(corsHeaders(request)).forEach(([name, value]) => headers.set(name, value));
  return headers;
}

function decodeXmlText(value) {
  return String(value || "")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&apos;/g, "'")
    .trim();
}

function xmlTagValues(xmlText, tagName) {
  const values = [];
  const pattern = new RegExp(`<${tagName}\\b[^>]*>([\\s\\S]*?)<\\/${tagName}>`, "gi");
  for (const match of String(xmlText || "").matchAll(pattern)) {
    const value = decodeXmlText(match[1]);
    if (value) {
      values.push(value);
    }
  }
  return values;
}

function buildObjectXmlUrl(dataProduct, objectId, project) {
  const target = new URL(`https://${CUS_HOST}/XML`);
  target.searchParams.set("class_str", dataProduct);
  target.searchParams.set("object_id", objectId);
  target.searchParams.set("project", project);
  return target;
}

async function mapWithConcurrency(items, concurrency, mapper) {
  const results = new Array(items.length);
  let nextIndex = 0;

  async function runWorker() {
    while (nextIndex < items.length) {
      const index = nextIndex;
      nextIndex += 1;
      results[index] = await mapper(items[index]);
    }
  }

  await Promise.all(Array.from({ length: Math.min(concurrency, items.length) }, runWorker));
  return results;
}

function validateObjectXmlChunk(payload) {
  const dataProduct = String(payload.dataProduct || "");
  const project = String(payload.project || "");
  const objectIds = Array.isArray(payload.objectIds) ? payload.objectIds : [];

  if (!/^[A-Za-z][A-Za-z0-9_]*$/.test(dataProduct)) {
    throw new Error("Invalid data product class");
  }
  if (!ALLOWED_PROJECTS.has(project)) {
    throw new Error("Invalid project");
  }
  if (!objectIds.length || objectIds.length > MAX_OBJECTS_PER_PROXY_CHUNK) {
    throw new Error(`Object chunk must contain 1-${MAX_OBJECTS_PER_PROXY_CHUNK} object IDs`);
  }

  const seen = new Set();
  const normalizedObjectIds = objectIds.map((objectId) => String(objectId || "").toUpperCase());
  normalizedObjectIds.forEach((objectId) => {
    if (!/^[0-9A-F]{16,64}$/.test(objectId) || seen.has(objectId)) {
      throw new Error("Invalid or duplicate EAS object ID");
    }
    seen.add(objectId);
  });

  return { dataProduct, project, objectIds: normalizedObjectIds };
}

async function resolveObjectXmlChunk(request, payload, headers) {
  let input;
  try {
    input = validateObjectXmlChunk(payload);
  } catch (error) {
    return jsonError(request, 400, error.message || "Invalid object XML chunk");
  }

  const results = await mapWithConcurrency(input.objectIds, OBJECT_FETCH_CONCURRENCY, async (objectId) => {
    try {
      const upstream = await fetch(buildObjectXmlUrl(input.dataProduct, objectId, input.project), { headers });
      if (!upstream.ok) {
        throw new Error(`EAS XML export returned ${upstream.status}`);
      }

      const xmlText = await upstream.text();
      const productId = xmlTagValues(xmlText, "ProductId")[0] || objectId;
      const fileNames = [
        ...new Set(
          xmlTagValues(xmlText, "DataStorage").flatMap((dataStorageXml) => xmlTagValues(dataStorageXml, "FileName"))
        ),
      ];
      if (!fileNames.length) {
        throw new Error("EAS XML export contained no FileName values");
      }
      return {
        objectId,
        files: fileNames.map((fileName) => ({ objectId, productId, fileName })),
      };
    } catch (error) {
      return { objectId, files: [], error: error.message || "EAS XML export failed" };
    }
  });

  const files = results.flatMap((result) => result.files);
  const errors = results
    .filter((result) => result.error)
    .map((result) => ({ objectId: result.objectId, message: result.error }));
  return jsonResponse(request, 200, { files, errors });
}

export default {
  async fetch(request) {
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders(request) });
    }

    if (request.method !== "POST") {
      return jsonError(request, 405, "Method not allowed");
    }

    const origin = request.headers.get("Origin");
    if (!origin || !isAllowedOrigin(origin)) {
      return jsonError(request, 403, `Origin not allowed: ${origin || "missing"}`);
    }

    let payload;
    try {
      payload = await request.json();
    } catch (_error) {
      return jsonError(request, 400, "Invalid JSON request body");
    }

    const authHeaderValue = normalizeBasicAuth(payload.authHeaderValue);
    if (!authHeaderValue) {
      return jsonError(request, 400, "Invalid Basic authentication header");
    }

    const headers = new Headers({ Authorization: authHeaderValue });
    if (payload.operation === "resolve-object-xml-chunk") {
      return resolveObjectXmlChunk(request, payload, headers);
    }
    if (payload.operation) {
      return jsonError(request, 400, "Unsupported proxy operation");
    }

    let target;
    try {
      target = new URL(payload.url);
    } catch (_error) {
      return jsonError(request, 400, "Invalid target URL");
    }

    if (!isAllowedTarget(target)) {
      return jsonError(request, 403, `Proxy target URL allowlist blocked ${target}`);
    }

    if (target.hostname === DSS_HOST && payload.requestHeaders?.Pragma === "DSSGET") {
      headers.set("Pragma", "DSSGET");
    }

    let upstream;
    try {
      upstream = await fetch(target, { headers });
    } catch (_error) {
      return jsonError(request, 502, `Upstream request failed: ${target.hostname}`);
    }

    return new Response(upstream.body, {
      status: upstream.status,
      statusText: upstream.statusText,
      headers: safeResponseHeaders(upstream, request),
    });
  },
};
