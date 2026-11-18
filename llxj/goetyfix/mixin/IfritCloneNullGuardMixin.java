package llxj.goetyfix.mixin;

import net.minecraft.world.entity.Entity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * goety_supreme 的 IfritClone.isAlliedTo 入口空判断（SRG: m_7307_）。
 *
 * 用字符串 target 而不是类引用：goety_supreme 是可选附属，字符串形式不产生编译期依赖，
 * 未安装时由软模式（required=false + defaultRequire=0）跳过，不崩溃。
 *
 * 缺陷形状（源码 IfritClone.java:213）：
 *   LivingEntity owner = getMaskOwner();
 *   if (owner != null && (... || other.isAlliedTo(owner) || ...)) ...
 * 第二句以参数 other 为接收者，other 为 null 且 owner 非空时直接 NPE。
 *
 * 可达性：registerGoals 先 removeAllGoals 清空目标选择器，再挂不带 setAlertOthers 的
 * HurtByTargetGoal，自身不会执行 alertOthers；alertOthers 又只向同精确类的邻居传 null，
 * 因此当前版本不可达，本 mixin 属防御性对齐（上游日后改动可能重新打开该路径）。
 *
 * 在入口返回 false 语义正确：null 实体不可能是盟友；其它参数原样透传。
 */
@Mixin(targets = "cn.blockforge.generated.forge1201goety.entity.IfritClone", remap = false)
public class IfritCloneNullGuardMixin {

    @Inject(method = "m_7307_", at = @At("HEAD"), cancellable = true, remap = false)
    private void goetyfix$nullGuardIsAlliedTo(Entity other, CallbackInfoReturnable<Boolean> cir) {
        if (other == null) {
            cir.setReturnValue(false);
        }
    }
}
