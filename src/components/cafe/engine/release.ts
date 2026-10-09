// Which release this is. The portfolio (Daniel's café) and the café builder are released
// separately: the builder's parts (build your own café, publishing, visiting someone's café) are
// only in a build with VITE_BUILD_ON=1. The dev server keeps them for Daniel, to make his own café.
export const BUILDER = import.meta.env.VITE_BUILD_ON === "1";
export const BUILDER_OR_DEV = BUILDER || import.meta.env.DEV;
