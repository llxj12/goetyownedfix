package llxj.goetyfix.mixin;

import net.minecraft.world.entity.Entity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * goetyominous 的 MurmurServant.isAlliedTo 入口空判断（SRG: m_7307_）。
 *
 * 字符串 target：goetyominous 为可选附属，不引入编译期依赖；未安装时软模式跳过。
 *
 * 缺陷形状（3.1.4 字节码）：
 *   if (getHeadUUID() != null)
 *       return entityIn.getUUID().equals(getHeadUUID());
 *   return super.isAlliedTo(entityIn);
 * getHeadUUID() 非空而 entityIn 为 null 时，直接对 null 调 getUUID() 抛 NPE。
 *
 * 可达性：MurmurServant 继承 Summoned，后者注册的 HurtByTargetGoal 未调用
 * setAlertOthers（m_26044_ 引用数为 0），自身不执行 alertOthers，收不到 null，
 * 当前不可达；本 mixin 属防御性对齐。
 */
@Mixin(targets = "com.qiuyue.goetyominous.common.entities.ally.am.MurmurServant", remap = false)
public class MurmurServantNullGuardMixin {

    @Inject(method = "m_7307_", at = @At("HEAD"), cancellable = true, remap = false)
    private void goetyfix$nullGuardIsAlliedTo(Entity entityIn, CallbackInfoReturnable<Boolean> cir) {
        if (entityIn == null) {
            cir.setReturnValue(false);
        }
    }
}
