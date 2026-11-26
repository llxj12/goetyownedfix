package llxj.goetyfix.mixin;

import net.minecraft.world.entity.Entity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/**
 * WitherNecromancer.isAlliedTo(Entity) 的空值守卫。
 *
 * Goety 的这个重写在收到 null 时会先解引用（entityIn.isAlliedTo(...) 等），
 * 而受伤反击目标 AI（HurtByTargetGoal）向同类传播伤害来源时可能传入 null
 * （lastHurtByMob 已被清空）。这里在方法入口拦截并返回 false：null 不可能是盟友。
 *
 * 目标类以字符串指定、remap = false：方法名属于 Goety 自身，不会被混淆，
 * 运行时保持 isAlliedTo 字面名。
 */
@Mixin(targets = "com.Polarice3.Goety.common.entities.hostile.WitherNecromancer", remap = false)
public class WitherNecromancerNullGuardMixin {

    @Inject(method = "isAlliedTo", at = @At("HEAD"), cancellable = true)
    private void goetyownedfix$guardNullAlly(Entity entityIn, CallbackInfoReturnable<Boolean> cir) {
        if (entityIn == null) {
            cir.setReturnValue(false);
        }
    }
}
