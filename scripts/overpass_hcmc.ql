[out:json][timeout:120];
(
  way["highway"~"^(primary|secondary|tertiary)$"](10.7500,106.6650,10.8000,106.7150);
  node["amenity"~"^(marketplace|bus_station|hospital|university)$"](10.7500,106.6650,10.8000,106.7150);
  way["amenity"~"^(marketplace|bus_station|hospital|university)$"](10.7500,106.6650,10.8000,106.7150);
  node["shop"="supermarket"](10.7500,106.6650,10.8000,106.7150);
  way["shop"="supermarket"](10.7500,106.6650,10.8000,106.7150);
);
(._;>;);
out body;