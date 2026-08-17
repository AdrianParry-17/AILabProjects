[out:json][timeout:180];
// Selector reconstructed from source metadata for the central-HCMC snapshot.
// The checksummed raw export, not a later query run, is the authoritative input.
// Runtime never calls Overpass; refreshes must be imported and reviewed offline.
(
  way["highway"~"^(primary|secondary|tertiary)(_link)?$"](10.750,106.665,10.800,106.715);
  nwr["amenity"~"^(hospital|university|marketplace|bus_station)$"](10.750,106.665,10.800,106.715);
  nwr["shop"="supermarket"](10.750,106.665,10.800,106.715);
);
(._;>;);
out body;
