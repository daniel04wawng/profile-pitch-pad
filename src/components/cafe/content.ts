// Draft copy for the café. Every "Placeholder" line gets replaced with real content.

export type Section = {
  kicker: string;
  title: string;
  body: string[];
  items?: { title: string; meta?: string; note?: string }[];
  links?: { label: string; href: string }[];
};

export const PROJECTS = [
  { id: "surplus", name: "Surplus", pastry: "croissant" },
  { id: "duet", name: "Duet", pastry: "macaron" },
  { id: "mira", name: "Mira AI", pastry: "cinnamon" },
  { id: "vgc", name: "VGC bench", pastry: "muffin" },
] as const;

export const SECTIONS: Record<string, Section> = {
  menu: {
    kicker: "Today's menu",
    title: "The blog",
    body: ["Placeholder. Posts go here, newest first, like a menu that changes daily."],
    items: [
      { title: "First post", meta: "coming soon" },
      { title: "Second post", meta: "coming soon" },
    ],
  },
  projects: {
    kicker: "The pastry case",
    title: "Fresh from the oven",
    body: ["Placeholder. Each pastry is a project. Tap one to read the story behind it."],
    items: PROJECTS.map((p) => ({ title: p.name, meta: "project" })),
  },
  now: {
    kicker: "Special of the day",
    title: "In the oven",
    body: ["Placeholder. What you're working on right now, plus anything freshly launched."],
  },
  about: {
    kicker: "Matcha latte",
    title: "About me",
    body: ["Placeholder. Who you are, in your own voice. One day this café is going to be real."],
  },
  work: {
    kicker: "Espresso bar",
    title: "Where I've worked",
    body: ["Placeholder."],
    items: [
      { title: "NimbleRx", meta: "Product" },
      { title: "KPMG", meta: "Consulting" },
      { title: "Vitalis", meta: "ESG" },
    ],
  },
  piano: {
    kicker: "The piano",
    title: "My music",
    body: [
      "Placeholder. Your piano pieces and compositions, each playable right here.",
      "Coming later: request a song and have a new café track generated for you.",
    ],
    items: [
      { title: "Piano piece", meta: "coming soon" },
      { title: "Café loop", meta: "playing on the record player", note: "placeholder" },
    ],
  },
  chill: {
    kicker: "Window seat",
    title: "Stay a while",
    body: ["Pull up a cushion, put the music on, and watch the street go by."],
  },
  books: {
    kicker: "The bookshelf",
    title: "Books I love",
    body: ["Placeholder. Your favorite books, with a line on why each one stuck."],
  },
  contact: {
    kicker: "Tip jar",
    title: "Say hi",
    body: ["The best way to reach me is email. I'm always up for coffee.", "Résumé: coming soon."],
    links: [
      { label: "Email", href: "mailto:daniel04wang@gmail.com" },
      { label: "LinkedIn", href: "https://www.linkedin.com/in/daniel04wang/" },
      { label: "GitHub", href: "https://github.com/daniel04wawng" },
      { label: "Devpost", href: "https://devpost.com/daniel04wang" },
    ],
  },
  "project:surplus": {
    kicker: "Fresh croissant",
    title: "Surplus",
    body: ["Placeholder. An AI agent that does the relationship work for you."],
  },
  "project:duet": {
    kicker: "Macarons",
    title: "Duet",
    body: [
      "Placeholder. Brain-computer interface that turns EEG signals into music.",
      "First place grand prize, Cal Hacks 11.0.",
    ],
  },
  "project:mira": {
    kicker: "Cinnamon roll",
    title: "Mira AI",
    body: ["Placeholder. Digital patient twin, shipped at NimbleRx."],
  },
  "project:vgc": {
    kicker: "Blueberry muffin",
    title: "VGC bench",
    body: ["Placeholder. A benchmark for AI agents playing competitive Pokémon."],
  },
};
