// 仕様: docs/spec/interface.md#7.1
import { nextTick, watch, type Ref } from 'vue'

export const NEAR_BOTTOM_THRESHOLD_PX = 40

export function isNearBottom(
  el: HTMLElement,
  threshold = NEAR_BOTTOM_THRESHOLD_PX,
): boolean {
  return el.scrollTop + el.clientHeight >= el.scrollHeight - threshold
}

export function useStickyBottomScroll(options: {
  listEl: Ref<HTMLElement | null>
  tailId: () => string | undefined
}): void {
  watch(
    options.tailId,
    async (newId, oldId) => {
      if (newId === oldId) {
        return
      }

      const el = options.listEl.value
      const shouldFollow = !el || isNearBottom(el)

      await nextTick()

      const listEl = options.listEl.value
      if (listEl && shouldFollow) {
        listEl.scrollTop = listEl.scrollHeight
      }
    },
  )
}
