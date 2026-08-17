# Data and service notice

The bundled canonical road-network snapshot is derived from OpenStreetMap data and is made available under the Open Data Commons Open Database License (ODbL) 1.0.

- Attribution: © OpenStreetMap contributors
- Copyright and license: <https://www.openstreetmap.org/copyright>
- Report a map issue: <https://www.openstreetmap.org/fixthemap>
- Repository reconstruction of the recorded selector: <code>scripts/overpass_hcmc.ql</code>; the checksummed raw export is authoritative.
- Canonical runtime snapshot: <code>backend/data/hcmc_delivery_osm_snapshot.json</code>
- OSM base timestamp recorded by the source export: <code>2026-08-05T16:31:02Z</code>
- Bounding box, in south/west/north/east order: <code>[10.750, 106.665, 10.800, 106.715]</code>

The bounded query covers selected primary, secondary and tertiary roads, their link roads, and five POI categories in central Ho Chi Minh City. It is not a citywide extract and does not imply complete street, alley, access or turn-restriction coverage.

The committed snapshot was normalized from temporary teammate exports by <code>scripts/import_hcmc_snapshot.py</code>. The temporary source directory <code>backend/data-tmp/</code> is git-ignored and is not read by the running API. Its source-file checksums are recorded in canonical metadata:

- processed graph SHA-256: <code>309798671DB1C7A29ACA7EEEA198C9E5903EAF8A71AED05F6DC47D9F690F41B1</code>;
- raw Overpass export SHA-256: <code>8F53BFF35B37E7B59234DEE15BB6CF14715C05460F80B0A568168A38009D60BD</code>.

OpenStreetMap contributes snapshot topology, coordinates, tags, road and POI names, geometry, direction information, and explicit numeric maxspeed values where available. Graph contraction, POI connectors, road-class speed fallbacks and component labels are derived transformations.

Baseline congestion, travel-time scenario multipliers, flood susceptibility, road-disruption flags, closures and risk values are deterministic educational simulations. They are not OpenStreetMap observations, live traffic measurements, forecasts or operational navigation advice.

The optional frontend basemap loads standard OSM tiles only for the visible interactive viewport and displays attribution. Do not bulk-download, prefetch or proxy standard tiles. Configure an appropriate provider for production or high-volume use.
