package llxj.goetyfix.mixin;

import net.minecraft.world.entity.Entity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Redirect;

/**
 * Defensive null-guard for the ignition call inside Goety's HellBlast explosion.
 *
 * Background (1.20.1 line, Goety 2.5.x): the anonymous SpellExplosion subclass
 * captured the projectile owner and called setSecondsOnFire() on it, so an
 * ownerless HellBlast crashed the server when its explosion hurt something.
 *
 * On 1.21.1 / Goety 3.1.5.1 the anonymous class no longer captures the owner:
 * explodeHurt ignites the entity that was damaged (its own method argument),
 * so that receiver cannot be null and this redirect is behaviour-neutral there.
 * It is kept as a cheap guard for 1.21.1 builds where the ignition receiver can
 * be null again (e.g. a future/older 3.1.x build that reintroduces the owner
 * capture): the damage applied by super.explodeHurt runs first and is untouched,
 * only the ignition is skipped when the receiver is null.
 *
 * Target class HellBlast$1 is Goety's own class and keeps its name at runtime;
 * NeoForge 1.21.1 runs on Mojang official names, so remap = false keeps the
 * literal Entity.igniteForSeconds(float) reference.
 */
@Mixin(targets = "com.Polarice3.Goety.common.entities.projectiles.HellBlast$1", remap = false)
public class HellBlastExplosionNullGuardMixin {

    @Redirect(
        method = "explodeHurt",
        at = @At(value = "INVOKE", target = "Lnet/minecraft/world/entity/Entity;igniteForSeconds(F)V"),
        require = 0,
        remap = false
    )
    private void goetyfix$skipNullIgnite(Entity target, float seconds) {
        if (target != null) {
            target.igniteForSeconds(seconds);
        }
    }
}
