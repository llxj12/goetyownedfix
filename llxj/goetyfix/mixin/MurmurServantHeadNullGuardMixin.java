package llxj.goetyfix.mixin;

import net.minecraft.world.entity.Entity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * goetyominous 的 MurmurServantHead.isAlliedTo 入口空判断（SRG: m_7307_）。
 *
 * 与 MurmurServant 同构，只是用 getBodyId()：
 *   if (getBodyId() != null) return entityIn.getUUID().equals(getBodyId());
 * getBodyId() 非空而 entityIn 为 null 时抛 NPE。
 *
 * 字符串 target：可选附属，无编译期依赖，未安装时软模式跳过。
 * 可达性同 MurmurServant（无 setAlertOthers），当前不可达，属防御性对齐。
 */
@Mixin(targets = "com.qiuyue.goetyominous.common.entities.ally.am.MurmurServantHead", remap = false)
public class MurmurServantHeadNullGuardMixin {

    @Inject(method = "m_7307_", at = @At("HEAD"), cancellable = true, remap = false)
    private void goetyfix$nullGuardIsAlliedTo(Entity entityIn, CallbackInfoReturnable<Boolean> cir) {
        if (entityIn == null) {
            cir.setReturnValue(false);
        }
    }
}
