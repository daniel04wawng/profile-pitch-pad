// Screens are data (public/cafe/screens.json), edited in the café editor's Screens tab.
// An object in the room opens a screen by id (its `hotspot`).

export type ScreenItem = {
  title: string;
  meta?: string; // the right-hand bit: a price on the menu, a date, a subtitle
  note?: string; // the longer text shown when you open the item
  sprite?: string; // pixel sprite from public/cafe/ui (pastries, cup, record)
  href?: string; // optional link for the item
  // photos and videos (a bake, a project's demo), shown in the item's gallery; paths under
  // public/cafe (media/...), uploaded in the editor
  media?: Media[];
  links?: { label: string; href: string }[]; // more buttons for the item (demo, code, write-up)
  tags?: string; // a project's stack or kind, comma separated
};
export type Media = { src: string; kind: "image" | "video" };

export type ScreenDef = {
  name: string; // what the editor's Screen picker shows
  template: Template;
  tone: Tone;
  kicker: string;
  title: string;
  body: string[];
  items: ScreenItem[];
  links: { label: string; href: string }[];
};

export type Screens = Record<string, ScreenDef>;

export const TEMPLATES = {
  case: "Glass case (browse items, like pastries)",
  menu: "Chalkboard menu (list with prices)",
  shelf: "Bookshelf (items are book spines)",
  music: "Music (record player + tracks)",
  receipt: "Receipt (contact links)",
  laptop: "Laptop (project boxes with demos)",
  text: "Text page (text, list, links)",
} as const;
export type Template = keyof typeof TEMPLATES;

export const TONES = { cream: "Cream paper", chalk: "Chalkboard", wood: "Dark wood" } as const;
export type Tone = keyof typeof TONES;

export const UI_SPRITES = [
  "pastry-cake", "pastry-cookies", "pastry-crepe", "pastry-bread", "pastry-pie", "pastry-cupcake", "pastry-tart",
  "pastry-croissant", "pastry-macaron", "pastry-cinnamon", "pastry-muffin", "pastry-donut", "cup", "record",
];

export function blankScreen(name: string): ScreenDef {
  return {
    name,
    template: "text",
    tone: "cream",
    kicker: name,
    title: name,
    body: ["Write something here."],
    items: [],
    links: [],
  };
}
