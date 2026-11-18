package llxj.goetyfix.mixin;

import com.mega.revelationfix.common.entity.cultists.MaverickServant;
import net.minecraft.world.entity.Entity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * RevelationFix 的 MaverickServant（“浪人”仆从）isAlliedTo 入口空判断（SRG: m_7307_）。
 *
 * 与 HereticServant 完全同构的漏点：
 *   MaverickServant.m_7307_(entityIn) 在拥有者非空时执行
 *       trueOwner.isAlliedTo(entityIn) 与 entityIn.isAlliedTo(trueOwner)；
 *   第二句以参数 entityIn 为接收者，entityIn 为 null 时直接抛 NPE。
 *
 * 可达性：MaverickServant 继承链为 RevelationFix.MaverickServant -> Goety.Maverick
 * -> Goety.Cultist，且其 registerGoals 首先调用 super，从而带上 Cultist 注册的
 * HurtByTargetGoal.setAlertOthers(...)（alertSameType = true）。因此它自己也会在
 * start() 里执行 alertOthers，把可能为 null 的 getLastHurtByMob() 传给同类邻居，
 * 与本补丁最初修复的真实崩溃链路完全相同。
 *
 * 在入口返回 false 是正确语义：null 实体不可能是盟友；其它参数原样透传。
 * 未安装 RevelationFix 时，软模式只跳过该 mixin 并告警，不影响启动。
 */
@Mixin(MaverickServant.class)
public class MaverickServantNullGuardMixin {

    @Inject(method = "m_7307_", at = @At("HEAD"), cancellable = true)
    private void goetyfix$nullGuardIsAlliedTo(Entity entityIn, CallbackInfoReturnable<Boolean> cir) {
        if (entityIn == null) {
            cir.setReturnValue(false);
        }
    }
}
