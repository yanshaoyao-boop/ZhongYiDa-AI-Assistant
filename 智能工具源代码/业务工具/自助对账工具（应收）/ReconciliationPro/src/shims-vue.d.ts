declare module "*.vue" {
  import type { DefineComponent } from "vue";
  const component: DefineComponent<{}, {}, any>;
  export default component;
}

declare module 'xlsx-js-style';
declare module 'lucide-vue-next';
declare module 'element-plus';
